// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VCHolderV2 {
    // Mappatura da una stringa (nome dell'issuer) a un singolo DID document
    mapping(string => string) public didDocuments;
    
    // Evento emesso quando un DID document è aggiunto o aggiornato
    event DIDDocumentAdded(string indexed issuerName, string didDocument);

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