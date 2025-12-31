// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Spedizione {
    struct spedizione {
        string id_spedizione;
        string descrizione;
        string indirizzo;
        string citta;
        string cap;
        string provincia;
        string grandezza;
        string metodo_pagamento;
        uint256 timestamp;       
    }

    mapping(string => spedizione) public spedizioni;
    event SpedizioneCreata(string indexed id_spedizione, string descrizione, string indirizzo);

    function creaSpedizione(
        string memory id_spedizione,
        string memory descrizione,
        string memory indirizzo,
        string memory citta,
        string memory cap,
        string memory provincia,
        string memory grandezza,
        string memory metodo_pagamento
    ) public {
        spedizioni[id_spedizione] = spedizione(
            id_spedizione, descrizione, indirizzo, citta, cap, provincia, grandezza, metodo_pagamento, block.timestamp);
        emit SpedizioneCreata(id_spedizione, descrizione, indirizzo);}
}
