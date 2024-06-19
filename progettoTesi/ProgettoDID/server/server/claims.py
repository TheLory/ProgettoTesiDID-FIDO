import datetime
import json

def get_current_time():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def create_university_degree_vc(did, DIDUtente, num_claims):
    cred = {
        "@context": "https://www.w3.org/2018/credentials/v1",
        "id": f"http://127.0.0.1:5001/universityDID{num_claims}",
        "type": ["VerifiableCredential"],
        "issuer": did,
        "issuanceDate": get_current_time(),
        "credentialSubject": {
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
            "id": DIDUtente,
        }

        
    }
    
    # Adding various types of claims dynamically at the root level
    for i in range(1, num_claims + 1):
        if i % 4 == 0:
            cred[f"claim{i}"] = f"string_value_{i}"
        elif i % 4 == 1:
            cred[f"claim{i}"] = i
        elif i % 4 == 2:
            cred[f"claim{i}"] = get_current_time()
        elif i % 4 == 3:
            cred[f"claim{i}"] = {"nested_claim": f"value{i}"}
    
    return cred

# Esempio di utilizzo
did = "did:example:123456"
DIDUtente = "did:example:abcdef"

claim_counts = [1, 10, 20, 30, 40, 50]
vc_list = []

for num_claims in claim_counts:
    credential = create_university_degree_vc(did, DIDUtente, num_claims)
    vc_list.append(credential)

# Stampa tutte le credenziali create
for vc in vc_list:
    print(json.dumps(vc, indent=2))
