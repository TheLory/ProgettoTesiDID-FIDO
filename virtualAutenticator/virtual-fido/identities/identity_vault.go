package identities

import (
	"bytes"
	"crypto/ecdsa"
	"crypto/x509"
	"encoding/json"
	"encoding/pem"
	"fmt"
	"net/http"

	"github.com/bulwarkid/virtual-fido/cose"
	"github.com/bulwarkid/virtual-fido/crypto"
	"github.com/bulwarkid/virtual-fido/webauthn"
)

type CredentialSource struct {
	Type             string
	ID               []byte
	PrivateKey       *cose.SupportedCOSEPrivateKey
	RelyingParty     *webauthn.PublicKeyCredentialRPEntity
	User             *webauthn.PublicKeyCrendentialUserEntity
	SignatureCounter int32
}

func (source *CredentialSource) CTAPDescriptor() webauthn.PublicKeyCredentialDescriptor {
	return webauthn.PublicKeyCredentialDescriptor{
		Type:       "public-key",
		ID:         source.ID,
		Transports: []string{},
	}
}

type IdentityVault struct {
	CredentialSources []*CredentialSource
}

func NewIdentityVault() *IdentityVault {
	sources := make([]*CredentialSource, 0)
	return &IdentityVault{CredentialSources: sources}
}

// AGGIUNTA DA ME PER STAMPARE VALORE DELLA CHIAVE PRIVATA IN FORMATO PEM
func printECDSAPrivateKey(privateKey *ecdsa.PrivateKey) {
	// Convertire la chiave privata ECDSA in un formato ASN.1 DER codificato
	derFormat, err := x509.MarshalECPrivateKey(privateKey)
	if err != nil {
		fmt.Println("Errore nella conversione della chiave privata ECDSA in DER:", err)
		return
	}

	// Creare un blocco PEM con la chiave privata codificata
	pemBlock := &pem.Block{
		Type:  "EC PRIVATE KEY",
		Bytes: derFormat,
	}

	// Convertire il blocco PEM in una stringa e stamparlo
	pemString := string(pem.EncodeToMemory(pemBlock))
	fmt.Println(pemString)
}

// CONVERSIONE DELLA CHIAVE IN FORMATO PEM PER ESSERE PASSATA A DIDKIT
func convertPrivateKeyToPEM(privateKey *ecdsa.PrivateKey) string {
	derFormat, err := x509.MarshalECPrivateKey(privateKey)
	if err != nil {
		fmt.Println("Errore nella conversione della chiave privata ECDSA in DER:", err)
		return ""
	}

	pemBlock := &pem.Block{
		Type:  "EC PRIVATE KEY",
		Bytes: derFormat,
	}

	return string(pem.EncodeToMemory(pemBlock))
}

// inviamo la chiave per ottenere indietro il did
func sendPrivateKeyToServer(privateKeyPEM string, RPname string) (string, error) {
	url := "http://localhost:5002/genereateDidFromPEM" // URL dell'endpoint del server Flask

	data := map[string]string{
		"privateKeyPEM": privateKeyPEM,
		"RPname":        RPname,
	}
	payload, err := json.Marshal(data)
	if err != nil {
		return "", err
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(payload))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "text/plain")

	client := &http.Client{}
	resp, err := client.Do(req) // Effettua una singola richiesta HTTP al server
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	// Leggi la risposta del server e deserializza il JSON per ottenere il DID
	var response struct {
		DID string `json:"did"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return "", fmt.Errorf("Errore durante la deserializzazione della risposta: %v", err)
	}

	return response.DID, nil // Restituisce il DID come valore della funzione
}

func (vault *IdentityVault) NewIdentity(relyingParty *webauthn.PublicKeyCredentialRPEntity, user *webauthn.PublicKeyCrendentialUserEntity) *CredentialSource {
	credentialID := crypto.RandomBytes(16)
	privateKey := crypto.GenerateECDSAKey()
	pemPrivateKey := convertPrivateKeyToPEM(privateKey)
	fmt.Println("@@@@@@@@@@@@@@@@@@@@")
	fmt.Println(relyingParty.Name)
	fmt.Println("@@@@@@@@@@@@@@@@@@@@")
	if relyingParty.Name == "Wallet" {
		// Invia la chiave privata al server
		_, _ = sendPrivateKeyToServer(pemPrivateKey, relyingParty.Name)
	}
	//didBytes := []byte(did)
	//fmt.Println(didBytes)
	//if err != nil {
	//	fmt.Printf("Errore nell'invio della chiave privata: %s\n", err)
	// Gestisci l'errore come necessario...
	//}
	cosePrivateKey := &cose.SupportedCOSEPrivateKey{ECDSA: privateKey}
	credentialSource := CredentialSource{
		Type:             "public-key",
		ID:               credentialID,
		PrivateKey:       cosePrivateKey,
		RelyingParty:     relyingParty,
		User:             user,
		SignatureCounter: 0,
	}

	vault.AddIdentity(&credentialSource)
	return &credentialSource
}

func (vault *IdentityVault) AddIdentity(source *CredentialSource) {

	vault.CredentialSources = append(vault.CredentialSources, source)

}

func (vault *IdentityVault) DeleteIdentity(id []byte) bool {
	for i, source := range vault.CredentialSources {
		if bytes.Equal(source.ID, id) {
			vault.CredentialSources[i] = vault.CredentialSources[len(vault.CredentialSources)-1]
			vault.CredentialSources = vault.CredentialSources[:len(vault.CredentialSources)-1]
			return true
		}
	}
	return false
}

func (vault *IdentityVault) GetMatchingCredentialSources(relyingPartyID string, allowList []webauthn.PublicKeyCredentialDescriptor) []*CredentialSource {
	sources := make([]*CredentialSource, 0)
	for _, credentialSource := range vault.CredentialSources {
		if credentialSource.RelyingParty.ID == relyingPartyID {
			if allowList != nil {
				for _, allowedSource := range allowList {
					if bytes.Equal(allowedSource.ID, credentialSource.ID) {
						sources = append(sources, credentialSource)
						break
					}
				}
			} else {
				sources = append(sources, credentialSource)
			}
		}
	}
	return sources
}

func (vault *IdentityVault) Export() []SavedCredentialSource {
	sources := make([]SavedCredentialSource, 0)
	for _, source := range vault.CredentialSources {
		key := cose.MarshalCOSEPrivateKey(source.PrivateKey)
		savedSource := SavedCredentialSource{
			Type:             source.Type,
			ID:               source.ID,
			PrivateKey:       key,
			RelyingParty:     *source.RelyingParty,
			User:             *source.User,
			SignatureCounter: source.SignatureCounter,
		}
		sources = append(sources, savedSource)
	}
	return sources
}

func (vault *IdentityVault) Import(sources []SavedCredentialSource) error {
	for _, source := range sources {
		key, err := cose.UnmarshalCOSEPrivateKey(source.PrivateKey)
		if err != nil {
			oldFormatKey, err := x509.ParseECPrivateKey(source.PrivateKey)
			if err != nil {
				return fmt.Errorf("Invalid private key for source: %w", err)
			}
			key = &cose.SupportedCOSEPrivateKey{ECDSA: oldFormatKey}
		}
		decodedSource := CredentialSource{
			Type:             source.Type,
			ID:               source.ID,
			PrivateKey:       key,
			RelyingParty:     &source.RelyingParty,
			User:             &source.User,
			SignatureCounter: source.SignatureCounter,
		}
		vault.AddIdentity(&decodedSource)
	}
	return nil
}
