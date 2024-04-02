from web3 import Web3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import os

# Funzione per caricare la chiave privata da un file .pem
def load_private_key_from_pem(file_path):
    with open(file_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,  # Fornisci qui una password se il tuo file PEM è cifrato
            backend=default_backend()
        )
    
    # Estrae la chiave privata in formato numerico e poi la converte in esadecimale
    private_key_hex = private_key.private_numbers().private_value.to_bytes(32, 'big').hex()
    return private_key_hex

# Percorso del file PEM che contiene la chiave privata
pem_file_path = './private_key.pem'

# Carica la chiave privata dal file PEM
private_key_hex = load_private_key_from_pem(pem_file_path)

# Utilizza la chiave privata per creare un account Web3
account = Web3().eth.account.create(private_key_hex)

# Ottiene l'indirizzo Ethereum dall'account
address = account.address

print(f"Indirizzo Ethereum: {address}")
print(f"Chiave Privata: {private_key_hex}")
# Creazione del DID ethr
did = f"did:ethr:{address}"
print(f"DID: {did}")
