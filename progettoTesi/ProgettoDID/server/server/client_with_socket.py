import socket
import json
import didkit  # Assicurati di avere questa libreria installata
import asyncio
from datetime import datetime
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

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

def create_university_degree_vc(did, DIDUtente):
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

async def issue_vc(data):
    try:
        didUtente = data.get('did')
        key_file = "server_private_key.pem"
        key = pem_to_jwk(key_file)
        verificationMethods = await didkit.key_to_verification_method("key", key)
        did = didkit.key_to_did("key", key)
        options = json.dumps({
            "proofPurpose": "assertionMethod",
            "verificationMethod": verificationMethods
        })
        cred = create_university_degree_vc(did, didUtente)
        verifiable_credential_signed = await didkit.issue_credential(
            json.dumps(cred),
            json.dumps({}),
            key)
        return verifiable_credential_signed
    except Exception as e:
        print(f"Errore durante l'emissione del VC: {e}")
        return {"error": str(e)}

def start_socket_server(host='localhost', port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            s.listen()
            print(f'Socket server listening on {host}:{port}')
            while True:
                conn, addr = s.accept()
                with conn:
                    print(f'Connected by {addr}')
                    data = conn.recv(4096)
                    if not data:
                        break
                    try:
                        request_data = json.loads(data.decode())
                        verifiable_credential_signed = asyncio.run(issue_vc(request_data))
                        response = json.dumps(verifiable_credential_signed)
                    except Exception as e:
                        response = json.dumps({'error': str(e)})
                    conn.sendall(response.encode())
        except socket.error as e:
            print(f"Errore nella connessione socket: {e}")

if __name__ == '__main__':
    start_socket_server()
