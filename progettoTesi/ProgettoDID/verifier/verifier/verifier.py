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





fido2.features.webauthn_json_mapping.enabled = True


app = Flask(__name__, static_url_path="")
app.secret_key = os.urandom(32)  # Used for session.
CORS(app)
rp = PublicKeyCredentialRpEntity(name="Progetto Tesi", id="localhost")
server = Fido2Server(rp)



@app.route("/")
def index():
    return redirect("/index.html")




ethereum_address = '0xE599D021BDD45ed5605e5aC8FF3DC02C14bB9e99'
private_key = '0x8d7443ef4d024e3217bc969fe957ed2ee2d72b805c91f4ec9a41e29006a0d9ca'

contract_address = '0x4d13C55283Fb372D58Cd7d510c689c047ca65ba7'
abi = json.loads('[{"anonymous": false,"inputs": [{"indexed": true,"internalType": "string","name": "issuerName","type": "string"},{"indexed": false,"internalType": "string","name": "didDocument","type": "string"}],"name": "DIDDocumentAdded","type": "event"},{"anonymous": false,"inputs": [{"indexed": false,"internalType": "string","name": "name","type": "string"},{"indexed": false,"internalType": "string","name": "publicKey","type": "string"}],"name": "PublicKeyAdded","type": "event"},{"anonymous": false,"inputs": [{"indexed": true,"internalType": "address","name": "issuer","type": "address"},{"indexed": true,"internalType": "uint256","name": "vcIndex","type": "uint256"},{"indexed": false,"internalType": "string","name": "vc","type": "string"}],"name": "VCPublished","type": "event"},{"inputs": [{"internalType": "string","name": "issuerName","type": "string"},{"internalType": "string","name": "didDocument","type": "string"}],"name": "addOrUpdateDIDDocument","outputs": [],"stateMutability": "nonpayable","type": "function"},{"inputs": [{"internalType": "string","name": "name","type": "string"},{"internalType": "string","name": "publicKey","type": "string"}],"name": "addPublicKey","outputs": [],"stateMutability": "nonpayable","type": "function"},{"inputs": [{"internalType": "string","name": "","type": "string"}],"name": "didDocuments","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "string","name": "name","type": "string"}],"name": "getPublicKey","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "address","name": "issuer","type": "address"}],"name": "getVCCount","outputs": [{"internalType": "uint256","name": "","type": "uint256"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "string","name": "","type": "string"}],"name": "publicKeys","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "string","name": "vc","type": "string"}],"name": "publishVC","outputs": [],"stateMutability": "nonpayable","type": "function"},{"inputs": [{"internalType": "string","name": "issuerName","type": "string"}],"name": "retrieveDIDDocument","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "address","name": "issuer","type": "address"},{"internalType": "uint256","name": "index","type": "uint256"}],"name": "retrieveVC","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "address","name": "issuer","type": "address"},{"internalType": "string","name": "content","type": "string"}],"name": "retrieveVCByContent","outputs": [{"internalType": "uint256","name": "","type": "uint256"},{"internalType": "bool","name": "","type": "bool"}],"stateMutability": "view","type": "function"},{"inputs": [{"internalType": "address","name": "","type": "address"},{"internalType": "uint256","name": "","type": "uint256"}],"name": "vcs","outputs": [{"internalType": "string","name": "","type": "string"}],"stateMutability": "view","type": "function"}]')
 
infura_url = 'http://127.0.0.1:7545'

@app.route('/valida_chiave_pubblica',methods = ['POST'])
async def valida_chiave_pubblica():
    file = request.files['vcFile']
    
    # Leggi il contenuto del file come stringa JSON
    vp_data = file.read().decode('utf-8')
    vp_data_string = vp_data.replace("\\", "")
    print(vp_data_string)
    # Decodifica la stringa JSON in un dizionario Python
    vp_dict = json.loads(vp_data_string[1:-1])
    print("################")
    print(type(vp_dict))  
    print("################")
  
    issuer_did = vp_dict['verifiableCredential'][0]['issuer']

    web3 = Web3(Web3.HTTPProvider(infura_url))
    if web3.is_connected():
        print("Connesso a Ethereum")
    else:
        print("Non connesso a Ethereum")
    contract = web3.eth.contract(address=contract_address, abi=abi)
    
    did_document = contract.functions.retrieveDIDDocument('issuer_server').call()
    issuer_did_bc = json.loads(did_document)['id']
    if (issuer_did == issuer_did_bc):
        return {"Response": "le chiavi corrispondono"}
    else:
        return{"Response": "Le chiavi NON corrispondoo"}
        


def main():
    app.run(ssl_context=("./localhost.crt","./localhost.key"), debug=True,port=5004)
 
    #app.run(ssl_context="adhoc", debug=True,port=5004)
    

if __name__ == "__main__":
    main()
    
