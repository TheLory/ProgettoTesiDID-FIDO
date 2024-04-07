from flask import Flask, request, jsonify, Response, redirect, render_template
import didkit
import os
from flask_cors import CORS
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import base64
import json
from jwcrypto import jwk
didCollection = []

private_key_file_path = 'Private key.pem'

key = ""

did = ""

verifiablePresentation = ""



app = Flask(__name__,static_url_path="")
CORS(app)

@app.route("/")
def index():
     return render_template('index.html')


def save_did_to_file(did):
    with open("wallet_did", "w") as file:
        file.write(did)


@app.route('/genereateDidFromPEM',methods = ['POST'] )
def genereateDidFromPEM():
     # Ricevi la chiave privata in formato PEM dalla richiesta
    global did_list
    all_data  = request.data
    print(all_data)
    pem_key = json.loads(all_data)["privateKeyPEM"].encode("utf-8")

    RPname = json.loads(all_data)['RPname']


    try:
        # Carica la chiave privata da PEM
        private_key = serialization.load_pem_private_key(
            pem_key,
            password=None,
            backend=default_backend()
        )

        # Ottieni i numeri della chiave privata e pubblica
        numbers = private_key.private_numbers()
        public_numbers = numbers.public_numbers

        # Estrai i valori x, y, e d
        d_int = numbers.private_value
        x_int = public_numbers.x
        y_int = public_numbers.y

        # Converti in formato JWK
        jwk_key = {
            "kty": "EC",
            "crv": "P-256",
            "x": base64.urlsafe_b64encode(x_int.to_bytes(32, 'big')).decode('utf-8').rstrip("="),
            "y": base64.urlsafe_b64encode(y_int.to_bytes(32, 'big')).decode('utf-8').rstrip("="),
            "d": base64.urlsafe_b64encode(d_int.to_bytes(32, 'big')).decode('utf-8').rstrip("="),
            "alg": "ES256",
            "use": "sig"
        }

       
        key2 = json.dumps(jwk_key, indent=2)
    

        print("Chiave privata in formato JWK:", key2)
        
        # Converti la chiave JWK in stringa JSON per didkit
        jwk_str = json.dumps(jwk_key)
        
        # Usa didkit per convertire la chiave JWK in un DID
        did = didkit.key_to_did("key", jwk_str)
        print("DID:", did)

        # Verifica se il file "wallet_did" esiste
        if RPname == "Wallet":
            if not os.path.exists("wallet_did.txt"):
                # Salva il DID nel file "wallet_did"
                save_did_to_file(did)

        #aggiungi_did_al_file(did)
        global didCollection 
        #didCollection = carica_dids_da_file()
        # Rispondi al mittente con il DID
        return jsonify({"did": did}), 200
    except Exception as e:
       
        return jsonify({"error": str(e)}), 400



vp_storage_file = 'vp_storage.json'

@app.route('/issueVP',methods=['POST'])
async def issueVP():
    global verifiablePresentation
    # Ottenere i dati della verifiable credential dalla richiesta JSON
    vc = request.json
    
    vp = {
        "@context": ["https://www.w3.org/2018/credentials/v1"],
        "type": ["VerifiablePresentation"],
        "verifiableCredential": [vc]
    }

    verification_method = await didkit.key_to_verification_method("key",key)       
    options = {
        "proofPurpose": "authentication",
        "verificationMethod": verification_method,
    }
    # Creare la verifiable presentation utilizzando DIDKit
    presentation = await didkit.issue_presentation(json.dumps(vp,ensure_ascii=False, indent=4), json.dumps(options,ensure_ascii=False,indent=4) , key)
    verifiablePresentation= presentation

    

     # Controlla se il file esiste, altrimenti crea un file vuoto con una lista vuota
    if not os.path.exists(vp_storage_file):
        with open(vp_storage_file, 'w') as file:
            json.dump([], file, ensure_ascii=False, indent=4)

    # Procede con la lettura e l'aggiornamento del file
    with open(vp_storage_file, 'r+') as file:
        try:
            stored_vps = json.load(file)
        except json.JSONDecodeError:
            stored_vps = []
        stored_vps.append(json.loads(presentation))
        file.seek(0)
        json.dump(stored_vps, file, ensure_ascii=False, indent=4)
        file.truncate()
   
    return presentation


@app.route('/validateVP', methods=['POST'])
async def verify_vp():
    
    vp = request.json

    did = ""

    with open('wallet_did', 'r') as file:
    # Leggo i contenuti del file
         did = file.readline().strip()

    # Decodifico il contenuto JSON in un dizionario Python
   
    public_key = await didkit.resolve_did(did,"{}")

    # Converti la stringa JSON in un dizionario Python
    data = json.loads(public_key)

    # Estrai la chiave pubblica JWK
    public_key_jwk = data["verificationMethod"][0]["publicKeyJwk"]

    # Estrai le coordinate x e y dalla chiave pubblica JWK
    x = public_key_jwk["x"]
    y = public_key_jwk["y"]

    # Decodifica le coordinate da base64
    x_bytes = base64.urlsafe_b64decode(x + '==')
    y_bytes = base64.urlsafe_b64decode(y + '==')

    # Stampa le coordinate della chiave pubblica
    
    jwk = {
        "kty": "EC",             # Tipo di chiave
        "crv": "P-256",          # Tipo di curva ellittica
        "x": base64.urlsafe_b64encode(x_bytes).decode('utf-8').rstrip("="),  # Coordinata x
        "y": base64.urlsafe_b64encode(y_bytes).decode('utf-8').rstrip("="),  # Coordinata y
        "alg": "ES256",          # Algoritmo
        "use": "sig"             # Uso
    }

    
    
    verification_method = await didkit.key_to_verification_method("key",json.dumps(jwk, indent=2))       

    if isinstance(vp, str):
        vp_dict = json.loads(vp.replace("'", "\""))  # Sostituisce le singole virgolette con doppie virgolette
    else:
        vp_dict = vp  # Se 'vp' è già un dizionario

    options = {
        "proofPurpose": "authentication",
        "verificationMethod": verification_method,
    }

    # Serializza 'vp_dict' e 'options' in stringhe JSON
    vp_json = json.dumps(vp_dict)
    options_json = json.dumps(options)


    validation_result = await didkit.verify_presentation(vp_json,options_json)
    print(validation_result)

    response = {"Response": validation_result}

    return jsonify(response)

richiestaVP = False

@app.route('/api/richiediVP', methods=['GET'])
def gestisciRichiestaVP():
    global richiestaVP
    richiestaVP = not richiestaVP
    return jsonify({'richiestaVP': richiestaVP}), 200


@app.route('/api/verificaRichiestaVP', methods=['GET'])
def verificaRichiestaVP():
    if richiestaVP:
        return jsonify({'autorizzato': True}), 200
    else:
        return jsonify({'autorizzato': False}), 403


@app.route('/api/recuperachaiveprivata', methods=['POST'])
def recuperaChiavePrivata():
    global richiestaVP
    global did
    global key
    if not richiestaVP:
        return jsonify({'errore': 'Non autorizzato'}), 403
    
    data = request.json
    # Assumendo che 'data' contenga le coordinate della chiave come {'curve': '...', 'd': '...', 'x': '...', 'y': '...'}
   
    richiestaVP = not richiestaVP

    try:
        
        print("################")
        d = data['d']
        x=  data['x']
        y=  data['y']

        d_bytes = int(d).to_bytes((int(d).bit_length() + 7) // 8, 'big')
        x_bytes = int(x).to_bytes((int(x).bit_length() + 7) // 8, 'big')
        y_bytes = int(y).to_bytes((int(y).bit_length() + 7) // 8, 'big')

        # Converti i bytes in base64
        d_base64 = base64.urlsafe_b64encode(d_bytes).decode('utf-8').rstrip("=")
        x_base64 = base64.urlsafe_b64encode(x_bytes).decode('utf-8').rstrip("=")
        y_base64 = base64.urlsafe_b64encode(y_bytes).decode('utf-8').rstrip("=")

        # Creazione di un oggetto JWK a partire dalle coordinate
        chiave = jwk.JWK(kty='EC', crv=data['curve'], d=d_base64, x=x_base64, y=y_base64)
        
        # Restituzione della chiave in formato JWK
        jwk_key = chiave.export()
        key = jwk_key
    
        did = didkit.key_to_did("key",jwk_key)
        print(did)
        print("################")
        return jsonify({'jwk': jwk_key}), 200
    except Exception as e:
        return jsonify({'errore': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5002)
