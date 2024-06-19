# Copyright (c) 2018 Yubico AB
# All rights reserved.
#
#   Redistribution and use in source and binary forms, with or
#   without modification, are permitted provided that the following
#   conditions are met:
#
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
Example demo server to use a supported web browser to call the WebAuthn APIs
to register and use a credential.

See the file README.adoc in this directory for details.

Navigate to https://localhost:5000 in a supported web browser.
"""
from fido2.webauthn import PublicKeyCredentialRpEntity, PublicKeyCredentialUserEntity, AttestedCredentialData
from fido2.server import Fido2Server
from fido2.cose import CoseKey
from flask import Flask, session, request, redirect, abort, jsonify, Response, render_template
from flask_cors import CORS
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import os
import random
import fido2.features
import base64
import didkit
import pickle
from pymongo import MongoClient
from bson.binary import Binary
import json
from datetime import datetime
import asyncio
import socket

# Connessione a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['DIDFIDO']
collection = db['WALLET']

fido2.features.webauthn_json_mapping.enabled = True
app = Flask(__name__, static_url_path="")
app.secret_key = os.urandom(32)  # Used for session.
CORS(app)
rp = PublicKeyCredentialRpEntity(name="Wallet", id="localhost")
server = Fido2Server(rp)


credentials = []

@app.route("/")
def index():
    return redirect("/index.html")


@app.route("/api/register/begin", methods=["POST"])
def register_begin():

    data = request.get_json()
    
        # Recupera le informazioni specifiche dall'oggetto JSON
  
    username = data.get('username')
    displayname = data.get('displayname')
    options, state = server.register_begin(
        PublicKeyCredentialUserEntity(
            id= os.urandom(32), # da cambiare con il did ricevuto direttamente da fido, oppure valutare se mettere il did nell'username
            name= username.encode('ascii'),
            display_name= displayname,
        ),

        challenge = os.urandom(32),
        user_verification="discouraged",
        authenticator_attachment="cross-platform",
      
    )

    session["state"] = state
    

    return jsonify(dict(options))


@app.route("/api/register/complete", methods=["POST"])
def register_complete():
    response = request.json
   # print("RegistrationResponse:", response)
    auth_data = server.register_complete(session["state"], response['response'])
  #  print("REGISTERED CREDENTIAL:", auth_data.credential_data)
    attested_cred_data = auth_data.credential_data
    attested_cred_data_serialized = pickle.dumps(attested_cred_data)
    collection.insert_one({'data': attested_cred_data_serialized,'username' : response['username']})
    global credentials
    credentials = getCredentialFromMongo()
    
    return jsonify({"status": "OK"})

def getCredentialFromMongo():
    updatedCredentials = []
    retrieved_documents = collection.find()
    for element in retrieved_documents:     
        attested_cred_data_serialized = element['data']
        username = element['username']
        
        attested_cred_data_retrieved = pickle.loads(attested_cred_data_serialized)
        updatedCredentials.append({
            'credential_data': attested_cred_data_retrieved,
            'username': username
        })

    return updatedCredentials

@app.route("/api/authenticate/begin", methods=["POST"])
def authenticate_begin():
    global credentials
    if not credentials:
        credentials = getCredentialFromMongo()
    if not credentials:
        abort(405)
    username = request.json.get('username')
  #  credential_data_list = [cred["credential_data"] for cred in credentials]
    credential_data = next((cred["credential_data"] for cred in credentials if cred["username"] == f"b'{username}'"), None)

    options, state = server.authenticate_begin([credential_data])
    session["state"] = state
    
    return jsonify(dict(options))


@app.route("/api/authenticate/complete", methods=["POST"])
def authenticate_complete():
    if not credentials:
        abort(404)
    
    response = request.json
    credential_data_list = [cred["credential_data"] for cred in credentials]

  #  print("AuthenticationResponse:", response)
    server.authenticate_complete(
        session.pop("state"),
        credential_data_list,
        response,
    )
    print("ASSERTION OK")
    return jsonify({"status": "OK"})

def pem_to_jwk(file_path):
    with open(file_path, 'rb') as key_file:
        private_key_pem = key_file.read()

    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None,
        backend=default_backend()
    )

    # Assicurati che la chiave caricata sia effettivamente una chiave privata EC
    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise ValueError("La chiave fornita non è una chiave privata EC.")

    # Ottieni i numeri sia della chiave privata che di quella pubblica
    private_numbers = private_key.private_numbers()
    public_numbers = private_numbers.public_numbers

    # Converti in formato JWK includendo il parametro della chiave privata
    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": base64.urlsafe_b64encode(public_numbers.x.to_bytes(32, byteorder='big')).decode('utf-8').rstrip("="),
        "y": base64.urlsafe_b64encode(public_numbers.y.to_bytes(32, byteorder='big')).decode('utf-8').rstrip("="),
        "d": base64.urlsafe_b64encode(private_numbers.private_value.to_bytes(32, byteorder='big')).decode('utf-8').rstrip("="),
        "alg": "ES256",
        "use": "sig"
    }

    return json.dumps(jwk, indent=2)

##########MOSTRA VC#############################################################################################################

vc_storage_file = 'vc_storage.json'

vp_storage_file = 'vp_storage.json'

@app.route('/vcmanagerVP')
def upload_and_display_vp():
 # Verifica se il file di storage esiste, altrimenti crea un file vuoto
    if not os.path.exists(vp_storage_file):
        with open(vp_storage_file, 'w') as file:
            json.dump([], file)
    
    # Carica i VC dal file di storage
    with open(vp_storage_file, 'r') as file:
        stored_vps = json.load(file)

    # Carica la pagina HTML per il caricamento del file e visualizza i VC
    return  render_template('vcmanager.html', vcs=stored_vps)    

#@app.route('/vcmanager2')  # Cambiato da '/' a '/vcmanager'
def upload_and_display_vc():
    # Verifica se il file di storage esiste, altrimenti crea un file vuoto
    if not os.path.exists(vc_storage_file):
        with open(vc_storage_file, 'w') as file:
            json.dump([], file)
    
    # Carica i VC dal file di storage
    with open(vc_storage_file, 'r') as file:
        stored_vcs = json.load(file)

    # Carica la pagina HTML per il caricamento del file e visualizza i VC
    return  render_template('vcmanager.html', vcs=stored_vcs)


@app.route('/vcmanager')
def upload_and_display_vcvp():
    # Verifica e crea il file di storage per VC se non esiste
    if os.path.exists("wallet_did.txt"):
        # Leggi il contenuto del file "wallet_did"
        with open("wallet_did.txt", "r") as file:
            did_content = file.read()
    else:
        # Se il file non esiste, impostiamo il contenuto del DID come vuoto
        did_content = ""

    if not os.path.exists(vc_storage_file):
        with open(vc_storage_file, 'w') as file:
            json.dump([], file)
    
    # Carica i VC dal file di storage
    with open(vc_storage_file, 'r') as file:
        stored_vcs = json.load(file)
    
    # Verifica e crea il file di storage per VP se non esiste
    if not os.path.exists(vp_storage_file):
        with open(vp_storage_file, 'w') as file:
            json.dump([], file)
    
    # Carica i VP dal file di storage
    with open(vp_storage_file, 'r') as file:
        stored_vps = json.load(file)
   
    # Carica la pagina HTML per il caricamento del file e visualizza sia i VC che i VP
    return render_template('vcmanager.html', vcs=stored_vcs, vps=stored_vps,did_content= did_content)

@app.route('/vcmanager/upload', methods=['POST'])  # Aggiustato per rispecchiare il nuovo percorso
def handle_upload():
    if 'file' not in request.files:
        return 'Nessun file selezionato', 400
    file = request.files['file']
    if file.filename == '':
        return 'Nessun file selezionato', 400
    if file and file.filename.endswith('.json'):
        # Legge il contenuto del VC
        vc_content = json.loads(file.read())

        # Carica i VC esistenti e aggiunge il nuovo VC
        if os.path.exists(vc_storage_file):
            with open(vc_storage_file, 'r') as file:
                stored_vcs = json.load(file)
        else:
            stored_vcs = []
        
        stored_vcs.append(vc_content)
      
        # Salva l'aggiornamento dei VC nel file
        with open(vc_storage_file, 'w') as file:
            json.dump(stored_vcs, file)

        return redirect('/vcmanager')
    else:
        return 'Formato file non supportato', 400

################################################################################################################################


@app.route('/genera-vp', methods=['POST'])
def genera_vp():
    vc_data = request.form.get('vc')
    if vc_data:
        #Todo inviare richiesta al client per impostare la ricezione della chiave
        #autneticazione
        #recupero della VP dal client

        # Processa la VC per generare un VP
        # Questo è un esempio, dovrai sostituirlo con la tua logica specifica
         return jsonify({"status": "success", "message": "VP generato correttamente."})
    else:
        return jsonify({"status": "error", "message": "Nessun dato VC fornito."}), 400


async def getPublicKey():
    global did_wallet_persistent
    global wallet_public_key
    try:
        # Apri il file "wallet_did" in modalità lettura
        with open("wallet_did.txt", "r") as file:
            # Leggi il contenuto del file e assegna il DID alla variabile did
            did_wallet_persistent = file.read().strip()
            publick_key_wallet = await didkit.resolve_did(did_wallet_persistent,"{}")
          
    except FileNotFoundError:
        # Se il file non esiste, imposta il DID su None
        did = None

def validateVP_blockchain():
    vc_data = request.json


########################
#SOCKET
def send_to_socket_server(action, data=None, host='localhost', port=65433):
    message = {"action": action, "data": data}
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(json.dumps(message).encode())
        response = s.recv(4096)
    return json.loads(response.decode())

@app.route('/issueVP', methods=['POST'])
def issueVP():
    vc_data = request.get_json()
   
    try:
        response = send_to_socket_server("issue_vp", vc_data)
       
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/richiediVP', methods=['GET'])
def gestisciRichiestaVP():
    try:
        response = send_to_socket_server("richiedi_vp")
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verificaRichiestaVP', methods=['GET'])
def verificaRichiestaVP():
    try:
        response = send_to_socket_server("verifica_richiesta_vp")
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recuperachaiveprivata', methods=['POST'])
def recuperaChiavePrivata():
    data = request.get_json()
    try:
        response = send_to_socket_server("recupera_chiave_privata", data)
        return jsonify(response), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def main():
   # print(__doc__)
    #app.run(ssl_context=None, debug=True, port=5003)
    asyncio.run(getPublicKey())
    app.run(ssl_context=("./cert.pem","./key.pem"), debug=True,port=5003,host="0.0.0.0")
    #app.run(ssl_context=None, debug=True,port=5001)



if __name__ == "__main__":
    main()
   
