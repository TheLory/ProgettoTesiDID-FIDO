// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VCHolderV2 {
    // Mappatura da un indirizzo a un array di VCs
    mapping(address => string[]) public vcs;

    // Evento emesso quando un VC è memorizzato
    event VCPublished(address indexed issuer, uint indexed vcIndex, string vc);

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
                return (i, true); // Restituisce l'indice della VC e true se trovata
            }
        }
        return (0, false); // Restituisce false se la VC non è stata trovata
    }


}
