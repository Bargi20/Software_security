// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Spedizione {
    struct spedizione {
        string descrizione;
        string indirizzo;
        string citta;
        string cap;
        string provincia;
        string grandezza;
        uint256 timestamp;
    }

    mapping(bytes32 => spedizione) public spedizioni;
    event SpedizioneCreata(bytes32 indexed id, string descrizione, string indirizzo);

    function creaSpedizione(
        bytes32 id,
        string memory descrizione,
        string memory indirizzo,
        string memory citta,
        string memory cap,
        string memory provincia,
        string memory grandezza
    ) public {
        spedizioni[id] = spedizione(descrizione, indirizzo, citta, cap, provincia, grandezza, block.timestamp);
        emit SpedizioneCreata(id, descrizione, indirizzo);
    }
}
