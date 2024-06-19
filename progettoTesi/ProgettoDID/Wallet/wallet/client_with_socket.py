import socket
import json
import base64
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import didkit  # Assicurati di avere questa libreria installata
import asyncio

richiestaVP = False
vp_storage_file = "vp_storage.json"
key_file = "server_private_key.pem"

def pem_to_jwk(pem_key):
    private_key = serialization.load_pem_private_key(
        pem_key,
        password=None,
        backend=default_backend()
    )

    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise ValueError("La chiave fornita non è una chiave privata EC.")

    private_numbers = private_key.private_numbers()
    public_numbers = private_numbers.public_numbers

    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": base64.urlsafe_b64encode(public_numbers.x.to_bytes(32, byteorder='big')).decode('utf-8').rstrip("="),
        "y": base64.urlsafe_b64encode(public_numbers.y.to_bytes(32, byteorder='big')).decode('utf-8').rstrip("="),
        "d": base64.urlsafe_b64encode(private_numbers.private_value.to_bytes(32, byteorder='big')).decode('utf-8').rstrip("="),
        "alg": "ES256",
        "use": "sig"
    }

    return jwk

async def handle_issue_vp(data):
    try:
        vc = data
        
        vp = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": ["VerifiablePresentation"],
            "verifiableCredential": [vc],
        }

        #with open(key_file, 'rb') as f:
        #    pem_key = f.read()
        
        #key = pem_to_jwk(pem_key)
        print(key)
        verification_method = await didkit.key_to_verification_method("key", key)
        options = {
            "proofPurpose": "authentication",
            "verificationMethod": verification_method,
        }
        

        presentation = await didkit.issue_presentation(
            json.dumps(vp, ensure_ascii=False, indent=4),
            json.dumps(options, ensure_ascii=False, indent=4),
            key
        )
        print(presentation)
        if not os.path.exists(vp_storage_file):
            with open(vp_storage_file, 'w') as file:
                json.dump([], file, ensure_ascii=False, indent=4)

        with open(vp_storage_file, 'r+') as file:
            try:
                stored_vps = json.load(file)
            except json.JSONDecodeError:
                stored_vps = []
            stored_vps.append(presentation)
            file.seek(0)
            json.dump(stored_vps, file, ensure_ascii=False, indent=4)
            file.truncate()

        return {"presentation": presentation}
    except Exception as e:
        return {"error": str(e)}

def handle_richiedi_vp():
    global richiestaVP
    richiestaVP = not richiestaVP
    return {'richiestaVP': richiestaVP}

def handle_verifica_richiesta_vp():
    return {'autorizzato': richiestaVP}

def handle_recupera_chiave_privata(data):
    global richiestaVP
    global did
    global key

    if not richiestaVP:
        return {'errore': 'Non autorizzato'}

    try:
        d = data['d']
        x = data['x']
        y = data['y']

        d_bytes = int(d).to_bytes((int(d).bit_length() + 7) // 8, 'big')
        x_bytes = int(x).to_bytes((int(x).bit_length() + 7) // 8, 'big')
        y_bytes = int(y).to_bytes((int(y).bit_length() + 7) // 8, 'big')

        d_base64 = base64.urlsafe_b64encode(d_bytes).decode('utf-8').rstrip("=")
        x_base64 = base64.urlsafe_b64encode(x_bytes).decode('utf-8').rstrip("=")
        y_base64 = base64.urlsafe_b64encode(y_bytes).decode('utf-8').rstrip("=")

        chiave = {
            "kty": "EC",
            "crv": data['curve'],
            "x": x_base64,
            "y": y_base64,
            "d": d_base64
        }

        jwk_key = json.dumps(chiave)
        key = jwk_key
        print(jwk_key)
        did = didkit.key_to_did("key", jwk_key)
        richiestaVP = not richiestaVP

        return {'jwk': jwk_key}
    except Exception as e:
        return {'errore': str(e)}

def start_socket_server(host='localhost', port=65433):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
                    action = request_data.get("action")
                    if action == "issue_vp":
                        result = asyncio.run(handle_issue_vp(request_data.get("data")))
                    elif action == "richiedi_vp":
                        result = handle_richiedi_vp()
                    elif action == "verifica_richiesta_vp":
                        result = handle_verifica_richiesta_vp()
                    elif action == "recupera_chiave_privata":
                        result = handle_recupera_chiave_privata(request_data.get("data"))
                    else:
                        result = {"error": "Azione non supportata"}
                    response = json.dumps(result)
                except Exception as e:
                    response = json.dumps({'error': str(e)})
                conn.sendall(response.encode())

if __name__ == '__main__':
    start_socket_server()
