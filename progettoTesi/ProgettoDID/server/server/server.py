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

credential1 = {
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://www.w3.org/2018/credentials/examples/v1"
  ],
  "id": "https://example.gov/credentials/3732",
  "type": ["VerifiableCredential", "PersonalIdentityCredential"],
  "issuer": "https://example.gov/issuers/14",
  "issuanceDate": "2020-10-20T19:73:24Z",
  "credentialSubject": {
    "id": "did:example:abcdef123456",
    "name": "Mario Rossi",
    "dateOfBirth": "1990-01-01",
    "nationality": "Italiana",
    "documentNumber": "AA123456"
  },
  "proof": {
    "type": "RsaSignature2018",
    "created": "2020-10-20T19:73:24Z",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "https://example.gov/issuers/keys/1",
    "jws": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ.eyJpc3MiOiJodHRwczovL2V4YW1wbGUuZ292L2lzc3VlcnMvMTQiLCJzdWIiOiJkaWQ6ZXhhbXBsZTphYmNkZWYxMjM0NTYiLCJqdGkiOiJodHRwczovL2V4YW1wbGUuZ292L2NyZWRlbnRpYWxzLzM3MzIifQ.Kyv7xg..."
  }
}

credential2 = {
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://www.w3.org/2018/credentials/examples/v1"
  ],
  "id": "https://example.edu/credentials/5656",
  "type": ["VerifiableCredential", "UniversityDegreeCredential"],
  "issuer": "https://example.edu/issuers/5656",
  "issuanceDate": "2021-06-20T19:53:24Z",
  "credentialSubject": {
    "id": "did:example:abcdef123456",
    "name": "Maria Bianchi",
    "degree": {
      "type": "BachelorDegree",
      "name": "Laurea in Informatica",
      "school": "Università degli Studi di Esempio"
    },
    "dateOfGraduation": "2021-06-20"
  },
  "proof": {
    "type": "RsaSignature2018",
    "created": "2021-06-20T19:53:24Z",
    "proofPurpose": "assertionMethod",
    "verificationMethod": "https://example.edu/issuers/keys/5656",
    "jws": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjU2NTYifQ.eyJpc3MiOiJodHRwczovL2V4YW1wbGUuZWR1L2lzc3VlcnMvNTY1NiIsInN1YiI6ImRpZDpleGFtcGxlOmFiY2RlZjEyMzQ1NiIsImp0aSI6Imh0dHBzOi8vZXhhbXBsZS5lZHUvY3JlZGVudGlhbHMvNTY1NiJ9.QWdN..."
  }
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
    print("RegistrationResponse:", response)
    auth_data = server.register_complete(session["state"], response)
    print("REGISTERED CREDENTIAL:", auth_data.credential_data)
    attested_cred_data = auth_data.credential_data
    attested_cred_data_serialized = pickle.dumps(attested_cred_data)
    collection.insert_one({'data': attested_cred_data_serialized})
    global credentials
    credentials = getCredentialFromMongo()
    
    return jsonify({"status": "OK"})

def getCredentialFromMongo():
    updatedCredentials = []
    retrieved_document = collection.find()
    for element in retrieved_document:     
        attested_cred_data_serialized = element['data']
        attested_cred_data_retrieved = pickle.loads(attested_cred_data_serialized)
        updatedCredentials.append(attested_cred_data_retrieved)

    return updatedCredentials

@app.route("/api/authenticate/begin", methods=["POST"])
def authenticate_begin():
    global credentials
    if not credentials:
        credentials = getCredentialFromMongo()
    if not credentials:
        abort(405)
    options, state = server.authenticate_begin(credentials)
    session["state"] = state
    
    return jsonify(dict(options))


@app.route("/api/authenticate/complete", methods=["POST"])
def authenticate_complete():
    if not credentials:
        abort(404)
    
    response = request.json
    print("AuthenticationResponse:", response)
    server.authenticate_complete(
        session.pop("state"),
        credentials,
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
#    print(f"Signed Credentials: {json.loads(verifiable_credential_signed)}")
    verfiableCredentials = verifiable_credential_signed
    return json.loads(verifiable_credential_signed)

@app.route("/api/downloadVC")
def downloadVC():
    json_data = json.dumps(verfiableCredentials)
    response = Response(json_data, mimetype='application/json')
    response.headers['Content-Disposition'] = 'attachment; filename=verifiableCredential.json'
    return response

def main():
   # print(__doc__)
    #app.run(ssl_context=None, debug=True, port=5001)
    
    app.run(ssl_context=("./localhost.crt","./localhost.key"), debug=True,port=5001)
    #app.run(ssl_context=None, debug=True,port=5001)


if __name__ == "__main__":
    main()
