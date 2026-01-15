// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Oracolo {

    struct Record {
        uint16 id;
        string nomeProva;
        string prob1; // "true", "false" o ""
        string prob2; // "true", "false" o ""
        string prob3; // "true", "false" o ""
        uint8 probabilitaCond; // scala 0-100
        uint16 idEvento1;
        uint16 idEvento2;
        uint16 idEvento3;
    }

    Record[] public records;

    // Inserisce tutti i record insieme, svuotando prima l'array
    function addRecords(Record[] memory newRecords) public {
        delete records;
        for (uint i = 0; i < newRecords.length; i++) {
            records.push(newRecords[i]);
        }
    }

    function getRecords() public view returns (Record[] memory) {
        return records;
    }

    function getRecordsCount() public view returns (uint) {
        return records.length;
    }

        // -------------------------------
    // Filtra per nomeProva e combinazione di prob1/prob2/prob3
    // -------------------------------
function getCijFiltered(
    string memory nomeProvaFilter,
    string memory boolProva,
    string memory prob1Filter,
    string memory prob2Filter,
    string memory prob3Filter
) public view returns (uint8) {
    for (uint i = 0; i < records.length; i++) {
        Record storage r = records[i];

        if (keccak256(bytes(r.nomeProva)) != keccak256(bytes(nomeProvaFilter))) {
            continue;
        }
        if (
            keccak256(bytes(r.prob1)) != keccak256(bytes(prob1Filter)) ||
            keccak256(bytes(r.prob2)) != keccak256(bytes(prob2Filter)) ||
            keccak256(bytes(r.prob3)) != keccak256(bytes(prob3Filter))
        ) {
            continue;
        }
        if (keccak256(bytes("true")) == keccak256(bytes(boolProva))) {
            return r.probabilitaCond;
        }
        // Restituisce il primo record che corrisponde ai filtri
        return 100 - r.probabilitaCond;
    }

    // Se nessun record corrisponde, possiamo decidere di restituire 0 oppure revert
    return 0;
    }
}
