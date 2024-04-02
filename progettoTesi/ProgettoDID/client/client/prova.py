import didkit
from flask_cors import CORS
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import base64
import json

# Modifica qui con il percorso al file della tua chiave privata
private_key_file_path = 'Private_key.pem'

def pem_to_jwk(file_path):
    with open(file_path, 'rb') as key_file:
        private_key_pem = key_file.read()

    private_key = serialization.load_pem_private_key(
        private_key_pem,
        password=None,
        backend=default_backend()
    )

    public_key = private_key.public_key()
    numbers = public_key.public_numbers()

    # Converti in formato JWK
    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": base64.urlsafe_b64encode(numbers.x.to_bytes(32, 'big')).decode('utf-8').rstrip("="),
        "y": base64.urlsafe_b64encode(numbers.y.to_bytes(32, 'big')).decode('utf-8').rstrip("="),
        "alg": "ES256",
        "use": "sig"
    }

    return json.dumps(jwk, indent=2)

def createDid():
    
    key =  pem_to_jwk(private_key_file_path)

    print(key)

    did =  didkit.key_to_did("key", key)
    
 #   issuer_VM = await didkit.key_to_verification_method("key", key)
    
    
   # print(issuer_VM)
    print(did)

def main():
    createDid()
if __name__ == '__main__':
    main()