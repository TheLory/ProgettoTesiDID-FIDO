from web3 import Web3
import os

# Genera una nuova coppia di chiavi e un indirizzo Ethereum utilizzando Web3.py
def generate_ethereum_account():
    # Utilizza os.urandom per generare un seed sicuro
    seed = os.urandom(32)
    
    # Crea un nuovo account Ethereum
    account = Web3().eth.account.create(seed)
    
    # Ottiene la chiave privata in formato esadecimale
    private_key = account._private_key.hex()
    
    # Ottiene l'indirizzo Ethereum
    address = account.address
    
    return address, private_key

# Esegui la funzione e stampa i risultati
address, private_key = generate_ethereum_account()
print(f"Indirizzo Ethereum: {address}")
print(f"Chiave Privata: {private_key}")

# Creazione del DID ethr
did = f"did:ethr:{address}"
print(f"DID: {did}")
