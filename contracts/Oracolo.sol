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
        uint256 probabilitaCond; // scala 0-100
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

//prende la probabilita condizionata A_ij che soddisfa il nomeProva e che combacia con i tre eventi
function getA_ij(
    string memory nomeProva,
    string memory evento1,
    string memory evento2,
    string memory evento3
) public view returns (uint256) {
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
        return r.probabilitaCond;
        }
        return 0;
    }
    

    function prob_spedizione_fallita(
        string memory checkEvento,
        string memory checkProva1, //GPS
        string memory checkProva2, //VEICOLO
        string memory checkProva3, //TRAFFICO
        string memory checkProva4, //CONFERMA CLIENTE
        string memory checkProva5, //CORRIERE
        uint256 priori1,
        uint256 priori2,
        uint256 priori3
    ) public view returns(uint256, uint256){

        uint256 numeratore = priori1;
        // adesso prendo tutte le prove di cui tutte le combinazioni in cui so evento1 ma non evento2
        
        // ----------GPS---------- 
        // GPS vero: ha sempre due eventi, quindi uno sempre vero e il secondo evento che puo essere vero o falso                  
        uint256 gps_tt = getA_ij("GPS", "true", "", "true");
        uint256 gps_tf = getA_ij("GPS", "true", "", "false");

        // mi serve per il denominatore
        uint256 gps_ft = getA_ij("GPS", "false", "", "true");
        uint256 gps_ff = getA_ij("GPS", "false", "", "false");

        // se GPS è falso mi servono i due complementari
        if(checkProva1.equal("false")){
            gps_tt = 100 - gps_tt;
            gps_tf = 100 - gps_tf;
        }


        //--------------VEICOLO-----------------
        uint256 veicolo_tt = getA_ij("Disponibilita veicolo", "true", "", "true");
        uint256 veicolo_tf = getA_ij("Disponibilita veicolo", "true", "", "false");

        uint256 veicolo_ft = getA_ij("Disponibilita veicolo", "false", "", "true");
        uint256 veicolo_ff = getA_ij("Disponibilita veicolo", "false", "", "false");

        if(checkProva2.equal("false")){
            veicolo_tt = 100 - veicolo_tt;
            veicolo_tf = 100 - veicolo_tf;
        }

        // -----------------TRAFFICO--------------
        uint256 traffico_tt = getA_ij("Traffico", "true", "", "true");
        uint256 traffico_tf = getA_ij("Traffico", "true", "", "false");

        uint256 traffico_ft = getA_ij("Traffico", "false", "", "true");
        uint256 traffico_ff = getA_ij("Traffico", "false", "", "false");

        if(checkProva3.equal("false")){
            traffico_tt = 100 - traffico_tt;
            traffico_tf = 100 - traffico_tf;
        }

        //------------------ CONFERMA CLIENTE ----------------------------
        // ne ha 4 perche ha tutti e 3 gli eventi, uno sempre vero e 4 combinazioni degli altri due
        uint256 confermacliente_ttt = getA_ij("Conferma Cliente", "true", "true", "true");
        uint256 confermacliente_ttf = getA_ij("Conferma Cliente", "true", "true", "false");
        uint256 confermacliente_tft = getA_ij("Conferma Cliente", "true", "false", "true");
        uint256 confermacliente_tff = getA_ij("Conferma Cliente", "true", "false", "false");

        // per il denominatore
        uint256 confermacliente_ftt = getA_ij("Conferma Cliente", "false", "true", "true");
        uint256 confermacliente_ftf = getA_ij("Conferma Cliente", "false", "true", "false");
        uint256 confermacliente_fft = getA_ij("Conferma Cliente", "false", "false", "true");
        uint256 confermacliente_fff = getA_ij("Conferma Cliente", "false", "false", "false");

        if(checkProva4.equal("false")){
            confermacliente_ttt = 100 - confermacliente_ttt;
            confermacliente_ttf = 100 - confermacliente_ttf;
            confermacliente_tft = 100 - confermacliente_tft;
            confermacliente_tff = 100 - confermacliente_tff;
        }

        // ------------------ CORRIERE ----------------------------
        uint256 corriere_tt = getA_ij("Disponibilita corriere", "true", "", "true");
        uint256 corriere_tf = getA_ij("Disponibilita corriere", "true", "", "false");

        uint256 corriere_ft = getA_ij("Disponibilita corriere", "false", "", "true");
        uint256 corriere_ff = getA_ij("Disponibilita corriere", "false", "", "false");

        if(checkProva5.equal("false")){
            corriere_tt = 100 - corriere_tt;
            corriere_tf = 100 - corriere_tf;
        }

        // se l'evento è falso, divneta 100 - priori1 e si cambiano le combinazioni del numeratore
        if(checkEvento.equal("false")){
            numeratore = 100 - priori1;
            numeratore = numeratore * ((priori2 * gps_ft * veicolo_ft * traffico_ft * corriere_ft) 
              + ((100-priori2) * gps_ff * veicolo_ff * traffico_ff * corriere_ft) 
              + (priori2 * priori3 * confermacliente_ftt) 
              + ((100-priori2)*priori3*confermacliente_fft) 
              + (priori2 * (100-priori3)*confermacliente_ftf) 
              + ((100-priori2)*(100-priori3)*confermacliente_fff));
        }
        else{ //se l'evento è vero
            numeratore = numeratore * ((priori2 * gps_tt * veicolo_tt * traffico_tt * corriere_tt) 
            + ((100-priori2) * gps_tf * veicolo_tf * traffico_tf * corriere_tf) 
            + (priori2 * priori3 * confermacliente_ttt) 
            + ((100 -priori2)*priori3*confermacliente_tft) 
            + (priori2 * (100-priori3)*confermacliente_ttf) 
            + ((100-priori2)*(100-priori3)*confermacliente_tff));
        }

        uint256 denominatore;
        denominatore = 
        (priori1 * priori2 * gps_tt * veicolo_tt * traffico_tt * corriere_tt) 
        + (priori1 * (100-priori2) * gps_tf * veicolo_tf * traffico_tf * corriere_tf) 
        + ((100-priori1) * priori2 * gps_ft * veicolo_ft * traffico_ft * corriere_ft) 
        + (((100-priori1) * (100-priori2) * gps_ff * veicolo_ff * traffico_ff * corriere_ff))
        + (priori1 * priori2* priori3 * confermacliente_ttt)
        + (priori1 * priori2 * (100-priori3)* confermacliente_ttf)
        + (priori1*(100-priori2)*priori3* confermacliente_tft)
        + (priori1*(100-priori2)*(100-priori3)* confermacliente_tff)
        + ((100-priori1)*priori2*priori3*confermacliente_ftt)
        + ((100-priori1)*priori2*(100-priori3)*confermacliente_ftf)
        + ((100-priori1)*(100-priori2)*priori3* confermacliente_fft)
        + ((100-priori1)*(100-priori2)*(100-priori3)* confermacliente_fff);

        // Siccome solidity non permette di fare matematica con numeri con la virgola, cioè i float, la divisione verrebbe troncata e il risultato sarebbe sempre 0, dato che esso è compreso tra 0 ed 1
        return (numeratore, denominatore);
    }
}

