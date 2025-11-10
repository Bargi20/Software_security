// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract ParityChecker {
    function isEven(uint number) public pure returns (string memory) {
        if (number % 2 == 0) {
            return "Pari";
        } else {
            return "Dispari";
        }
    }
    function stampaMess(string memory messaggio) public pure returns (string memory){
        return messaggio;
    }
}