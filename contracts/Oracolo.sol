// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Oracolo {

    struct Record {
        uint16 id;
        string nomeProva;
        bool prob1;
        bool prob1Exists;
        bool prob2;
        bool prob2Exists;
        bool prob3;
        bool prob3Exists;
        string probabilitaCond; // messo stringa per evitare problemi di conversione (float non si puo usare su solidity)
        uint16 idEvento1;
        uint16 idEvento2;
        uint16 idEvento3;
    }

    Record[] public records;

    // Inserisce tutti i record insieme, svuotando prima l'array
    function addRecords(Record[] memory newRecords) public {
        delete records; // Pulisce l'array esistente (altrimenti li appende sotto e si duplicano gli elementi)
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
}
