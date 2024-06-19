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
from flask import Flask, session, request, redirect, abort, jsonify, Response
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
from web3 import Web3
import json
from eth_account import Account
import asyncio

serverKey = {
  "kty": "RSA",
  "use": "sig",
  "kid": "12345",
  "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LZK4ugt4e48WzcgyM9dAkk1aGf8H3AZiSn7yVuvPbk3TWvgdX5guj4XQiHf4yVzPLWk6ACloYDl2abA2d7pFifcRY6t7NwT3fJv2PQFyS4tTVPIFm6QLv7Z4TeEUo9H2mkGvUQ",
  "e": "AQAB",
  "alg": "RS256",
  "d": "X4cTteJY_gn4FYPsXB8rdXKTCtXMI3OKXnS14G3GgR5K...saQ",
  "p": "_xcC2-8LNKHP...0Q",
  "q": "5nU8QoH...2T0",
  "dp": "BwKsBn...PjQ",
  "dq": "h_6mI...kjg",
  "qi": "I3bhA...89M"
}




# Connessione a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['DIDFIDO']
collection = db['DIDFIDO']


fido2.features.webauthn_json_mapping.enabled = True


app = Flask(__name__, static_url_path="")
app.secret_key = os.urandom(32)  # Used for session.
CORS(app)
rp = PublicKeyCredentialRpEntity(name="Progetto Tesi", id="localhost")
server = Fido2Server(rp)


# Registered credentials are stored globally, in memory only. Single user
# support, state is lost when the server terminates.
credentials = [] ## sostituire con db locale

verfiableCredentials = ""

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
            id= os.urandom(16), # da cambiare con il did ricevuto direttamente da fido, oppure valutare se mettere il did nell'username
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
    print("RegistrationResponse:", response)
    auth_data = server.register_complete(session["state"], response['response'])
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
   # print("AuthenticationResponse:", response)
    credential_data_list = [cred["credential_data"] for cred in credentials]
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

def get_current_time():
    return datetime.now().replace(microsecond=0).isoformat() + "Z"
issuer_name = 'issuer_server'
def create_university_degree_vc(did,DIDUtente):

    cred = {
        "@context": "https://www.w3.org/2018/credentials/v1",
        "id": "http://127.0.0.1:5001/universityDID",
        "type": ["VerifiableCredential"],
        "issuer": did,
        "issuanceDate": get_current_time(),
        "credentialSubject": {
            "id": DIDUtente,
        }
    }

    return cred

contract_address = '0x4d13C55283Fb372D58Cd7d510c689c047ca65ba7'
abi = json.loads('[{"anonymous": false,"inputs": [{"indexed": true,"internalType": "string","name": "issuerName","type": "string"},{"indexed": false,"internalType": "string","name": "didDocument","type": "string"}],"name": "DIDDocumentAdded","type": "event"},{"anonymous": false,"inputs": [{"indexed": false,"internalType": "string","name": "name","type": "string"},{"indexed": false,"internalType": "string","name": "publicKey","type": "string"}],"name": "PublicKeyAdded","type": "event"},{"anonymous": false,"inputs": [{"indexed": true,"internalType": "address","name": "issuer","type": "address"},{"indexed": true,"internalType": "uint256","name": "vcIndex","type": "uint256"},{"indexed": false,"internalType": "string","name": "vc","type": "string"}],"name": "VCPublished","type": "event"},{"inputs": [{"internalType": "string","name": "issuerName","type": "string"},{"internalType": "string","name": "didDocument","type": "string"}],"name": "addOrUpdateDIDDocument","outputs": [],"stateMutability": "nonpayable","type": "function"},{"inputs": [{"internalType": "string","name": "name","type": "string"},{"internalType": "string","name": "publicKey","type": "string"}],"name": "addPublicKey","outputs": [],"stateMutability": "nonpayable","type": "function"},{"inputs": [{"internalType": "string","name": "","type": "string"}],"name": "didDocuments","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "string","name": "name","type": "string"}],"name": "getPublicKey","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "address","name": "issuer","type": "address"}],"name": "getVCCount","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "string","name": "","type": "string"}],"name": "publicKeys","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "string","name": "vc","type": "string"}],"name": "publishVC","outputs": [],"stateMutability": "nonpayable","type": "function"},{"inputs": [{"internalType": "string","name": "issuerName","type": "string"}],"name": "retrieveDIDDocument","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "address","name": "issuer","type": "address"},{"internalType": "uint256","name": "index","type": "uint256"}],"name": "retrieveVC","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "address","name": "issuer","type": "address"},{"internalType": "string","name": "content","type": "string"}],"name": "retrieveVCByContent","outputs": [{"internalType": "uint256","name": "","type": "uint256"},{"internalType": "bool","name": "","type": "bool"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "address","name": "","type": "address"},{"internalType": "uint256","name": "","type": "uint256"}],"name": "vcs","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"}]')


def pubblica_vc_su_bc(verifiable_credential_signed):

    w3 = Web3(Web3.HTTPProvider('HTTP://127.0.0.1:7545'))
    # Verifica della connessione
    if w3.is_connected():
        print("Connesso alla blockchain Ethereum.")
    else:
        print("Non connesso alla blockchain Ethereum.")
        exit()

    # Dati dello smart contract
   
    # Creazione dell'istanza dello smart contract
    contract = w3.eth.contract(address=contract_address, abi=abi)


    # Account Ethereum e chiave privata (usa il tuo account e la tua chiave privata)
    ethereum_address = '0x9f94951c1C6118027fB69B4d9A88d30e0ebFcee1'
    private_key = '0x33c77c244f913d5a6e615dce5cca6bb9b52816c2ebd58dcd522e88c2987007d8'

    # Genera una nuova coppia di chiavi per l'account Ethereum (o usa un account esistente)
    account = Account.from_key(private_key)

    # Estrai l'indirizzo Ethereum e la chiave privata
    ethereum_address = account.address

    vc_string = json.dumps(verifiable_credential_signed)
   

    # Preparazione della transazione
    nonce = w3.eth.get_transaction_count(ethereum_address)
    tx = contract.functions.publishVC(json.loads(vc_string)).build_transaction({
        'chainId': 1337,  # Sostituisci con il chainId corretto
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': nonce,
    })

    index = contract.functions.getVCCount(ethereum_address).call()

    print('Indice VC: ', index)

    # Firma e invia la transazione
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Attendi la ricevuta della transazione
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"VC pubblicato sulla blockchain. Hash della transazione: {tx_receipt.transactionHash.hex()}")

    return index

@app.route("/api/issueVC",methods = ["POST"])
async def issueVC():
    data = request.get_json()
    didUtente = data.get('did')
    global verfiableCredentials
    key_file = "server_private_key.pem"
    key = pem_to_jwk(key_file)
    verificationMethods = await didkit.key_to_verification_method("key",key)
    #jwk = didkit.generate_ed25519_key()
    did = didkit.key_to_did("key", key)
    options = json.dumps ({
         "proofPurpose": "assertionMethod",
         "verificationMethod" : verificationMethods
    })
    cred = create_university_degree_vc(did,didUtente)  
    verifiable_credential_signed = await didkit.issue_credential(
        json.dumps(cred),
        json.dumps({}),
        key)

    verfiableCredentials = verifiable_credential_signed
    index = pubblica_vc_su_bc(verifiable_credential_signed)
    return json.dumps(verifiable_credential_signed)



async def pubblica_did_document():

    key_file = "server_private_key.pem"
    key = pem_to_jwk(key_file)
    did_server = didkit.key_to_did("key",key)
    input_metadata = '{"context": "https://www.w3.org/ns/did/v1"}'
    did_server_document = await didkit.resolve_did(did_server,input_metadata)
    print(did_server_document)
    name = "Issuer_numero_1"
    public_key = str(json.loads(key)["x"]+":"+json.loads(key)["y"])
    print(type(public_key))
    print(public_key)
    

    w3 = Web3(Web3.HTTPProvider('HTTP://127.0.0.1:7545'))    # Verifica della connessione
    if w3.is_connected():
        print("Connesso alla blockchain Ethereum.")
    else:
        print("Non connesso alla blockchain Ethereum.")
        exit()
    

    contract = w3.eth.contract(address=contract_address, abi=abi)

   
    account_address = '0x9f94951c1C6118027fB69B4d9A88d30e0ebFcee1'
    private_key = '0x33c77c244f913d5a6e615dce5cca6bb9b52816c2ebd58dcd522e88c2987007d8'
    # Prepara la transazione
    nonce = w3.eth.get_transaction_count(account_address)
    transaction = contract.functions.addOrUpdateDIDDocument(issuer_name,did_server_document).build_transaction({
        'chainId': 1337,
        'gas': 2000000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': nonce,
    })

    # Firma e invia la transazione
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)
    txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)

    # Ottieni l'hash della transazione
    print("Hash della transazione:", w3.to_hex(txn_hash))
    return




async def main():
   # print(__doc__)
    #app.run(ssl_context=None, debug=True, port=5001)
    await pubblica_did_document()
    
    app.run(ssl_context=("./localhost.crt","./localhost.key"), debug=True,port=5001)
    #app.run(ssl_context=None, debug=True,port=5001)
    

if __name__ == "__main__":
    asyncio.run(main())
    
