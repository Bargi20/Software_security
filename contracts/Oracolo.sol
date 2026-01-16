// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";

contract Oracolo {
    using Strings for string;
    struct Record {
        uint16 id;
        string nomeProva;
        string evento1; // "true", "false" o ""
        string evento2; // "true", "false" o ""
        string evento3; // "true", "false" o ""
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
function getA_ij(
    string memory nomeProva,
    string memory checkProva,
    string memory evento1,
    string memory evento2,
    string memory evento3
) public view returns (uint8) {
    for (uint i = 0; i < records.length; i++) {
        Record storage r = records[i];
        // Se non coincide il nomeProva, il record viene scartato, il ciclo passa direttamente all’iterazione successiva
        if (!(r.nomeProva.equal(nomeProva))) {
            continue; // interrompe l’iterazione corrente del ciclo e passa subito alla successiva.
        }

        // Se non coincide almeno uno dei tre eventi, il record viene scartato, il ciclo passa direttamente all’iterazione successiva
        if (
            !(r.evento1.equal(evento1)) ||
            !(r.evento2.equal(evento2)) ||
            !(r.evento3.equal(evento3))
        ) {
            continue;
        }
        // mi ritorna la probabilitaCond del record se prova è "true"
        if (checkProva.equal("true")) {
            return r.probabilitaCond;
        }
        // altrimenti mi torna il complementare
        return 100 - r.probabilitaCond;
    }
    // Serve solo per dire alla funzione che almeno un valore intero ritornerà
    return 0;
    }
}
