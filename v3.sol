// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VCHolderV2 {
    // Mappatura da un indirizzo a un array di VCs
    mapping(address => string[]) public vcs;

    // Mappatura da una stringa (nome) a una chiave pubblica
    mapping(string => string) public publicKeys;

    // Mappatura da una stringa (nome dell'issuer) a un singolo DID document
    mapping(string => string) public didDocuments;
    
    // Evento emesso quando un VC è memorizzato
    event VCPublished(address indexed issuer, uint indexed vcIndex, string vc);

    // Evento emesso quando una chiave pubblica è aggiunta
    event PublicKeyAdded(string name, string publicKey);

    // Evento emesso quando un DID document è aggiunto o aggiornato
    event DIDDocumentAdded(string indexed issuerName, string didDocument);

    // Funzione per pubblicare un nuovo VC
    function publishVC(string memory vc) public {
        vcs[msg.sender].push(vc);
        emit VCPublished(msg.sender, vcs[msg.sender].length - 1, vc);
    }

    // Funzione per recuperare una VC dato un emittente e l'indice della VC
    function retrieveVC(address issuer, uint index) public view returns (string memory) {
        require(index < vcs[issuer].length, "Index out of bounds");
        return vcs[issuer][index];
    }

    // Funzione per ottenere il numero totale di VCs per un emittente
    function getVCCount(address issuer) public view returns (uint) {
        return vcs[issuer].length;
    }

    // Funzione per recuperare una VC sulla base del suo contenuto
    function retrieveVCByContent(address issuer, string memory content) public view returns (uint, bool) {
        for(uint i = 0; i < vcs[issuer].length; i++) {
            if(keccak256(bytes(vcs[issuer][i])) == keccak256(bytes(content))) {
                return (i, true);
            }
        }
        return (0, false);
    }

    // Funzione per aggiungere una nuova chiave pubblica
    function addPublicKey(string memory name, string memory publicKey) public {
        publicKeys[name] = publicKey;
        emit PublicKeyAdded(name, publicKey);
    }

    // Funzione per recuperare la chiave pubblica dato un nome
    function getPublicKey(string memory name) public view returns (string memory) {
        require(bytes(publicKeys[name]).length != 0, "No public key found for this name");
        return publicKeys[name];
    }

    // Funzione per aggiungere o aggiornare un DID document
    function addOrUpdateDIDDocument(string memory issuerName, string memory didDocument) public {
        require(bytes(didDocument).length > 0, "DID document cannot be empty");
        didDocuments[issuerName] = didDocument;
        emit DIDDocumentAdded(issuerName, didDocument);
    }

    // Funzione per recuperare il DID document di un dato issuer (nome)
    function retrieveDIDDocument(string memory issuerName) public view returns (string memory) {
        require(bytes(didDocuments[issuerName]).length != 0, "No DID document found for this name");
        return didDocuments[issuerName];

    }
}
