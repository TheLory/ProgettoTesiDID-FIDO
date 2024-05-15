from pymongo import MongoClient
from bson.binary import Binary

# Connessione a MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['DIDFIDO']
collection = db['DIDFIDO']

# Dati da inserire, con chiavi convertite in stringhe
credentials = {
    'aaguid': "00000000-0000-0000-0000-000000000000",
    'credential_id': Binary(b'f[4x\xd417\x0cz\x8f\x96\xe6\x9f4\x83\xach\xb9\xee\xbcO>s\xda\xe8\xf6J\x12\xa7s\xa0\xbe'),
    'public_key': {
        "1": 2,
        "3": -7,
        "-1": 1,
        "-2": Binary(b'\x10\x9f`\xc1\xf9\xd3k\xde\xa8{P\x07\x86\xe2\xb1\xdcG\xcfFT\xcc\xf3\xca\x89\x94|H-7\x10\xbeP'),
        "-3": Binary(b'\xf3r,\xa4\xbd\x8b P\xf6i%\xea\xeb\xf8\xacq\x93\xfed\x9czP\x0e"w/f.\xa7\xd29\x96')
    }
}

# Inserimento dei dati
collection.insert_one(credentials)

print("Dati inseriti con successo.")
