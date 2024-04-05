from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# Genera una chiave privata EC con la curva P-256
private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

# Serializza la chiave privata in formato PEM
pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
)

# Salva la chiave privata su un file
with open('server_private_key.pem', 'wb') as pem_file:
    pem_file.write(pem)

print("Chiave privata EC P-256 salvata su 'server_private_key.pem'")
