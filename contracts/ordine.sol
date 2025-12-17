// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.19;

contract Ordine {

    struct OrdineData {
        string id;
        string indirizzoConsegna;
        string nomeCliente;
        string cognomeCliente;
        string citofono;
    }

    mapping(string => OrdineData) private ordini;

    event OrdineCreato(
        string id,
        string indirizzoConsegna,
        string nomeCliente,
        string cognomeCliente,
        string citofono
    );

    function creaOrdine(
        string memory _id,
        string memory _indirizzoConsegna,
        string memory _nomeCliente,
        string memory _cognomeCliente,
        string memory _citofono
    ) public {
        ordini[_id] = OrdineData(
            _id,
            _indirizzoConsegna,
            _nomeCliente,
            _cognomeCliente,
            _citofono
        );

        emit OrdineCreato(
            _id,
            _indirizzoConsegna,
            _nomeCliente,
            _cognomeCliente,
            _citofono
        );
    }

    function getOrdine(string memory _id)
        public
        view
        returns (
            string memory,
            string memory,
            string memory,
            string memory,
            string memory
        )
    {
        OrdineData memory o = ordini[_id];
        return (
            o.id,
            o.indirizzoConsegna,
            o.nomeCliente,
            o.cognomeCliente,
            o.citofono
        );
    }
}
