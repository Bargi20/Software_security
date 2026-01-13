// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ConditionalProbabilityOracle {

    /// @notice indirizzo autorizzato (oracle off-chain)
    address public oracle;

    /// @notice probabilità condizionate P(B | A)
    /// probabilities[A][B] = valore (es. 7500 = 75.00%)
    mapping(uint256 => mapping(uint256 => uint32)) private probabilities;

    /// @notice flag inizializzazione
    bool public initialized;

    /// EVENTS
    event OracleUpdated(address oracle);
    event ProbabilitySet(uint256 indexed eventA, uint256 indexed eventB, uint32 value);
    event Initialized();

    /// MODIFIERS
    modifier onlyOracle() {
        require(msg.sender == oracle, "Not authorized oracle");
        _;
    }

    modifier notInitialized() {
        require(!initialized, "Already initialized");
        _;
    }

    /// CONSTRUCTOR
    constructor(address _oracle) {
        require(_oracle != address(0), "Invalid oracle");
        oracle = _oracle;
    }

    /// ADMIN — aggiorna oracle (opzionale)
    function setOracle(address _oracle) external onlyOracle {
        require(_oracle != address(0), "Invalid oracle");
        oracle = _oracle;
        emit OracleUpdated(_oracle);
    }

    /// ORACLE — inizializzazione batch
    function initializeProbabilities(
        uint256[] calldata eventA,
        uint256[] calldata eventB,
        uint32[] calldata values
    )
        external
        onlyOracle
        notInitialized
    {
        require(
            eventA.length == eventB.length && eventB.length == values.length,
            "Length mismatch"
        );

        for (uint256 i = 0; i < eventA.length; i++) {
            probabilities[eventA[i]][eventB[i]] = values[i];
            emit ProbabilitySet(eventA[i], eventB[i], values[i]);
        }

        initialized = true;
        emit Initialized();
    }

    /// ORACLE — update singolo (post-inizializzazione)
    function updateProbability(
        uint256 eventA,
        uint256 eventB,
        uint32 value
    )
        external
        onlyOracle
    {
        probabilities[eventA][eventB] = value;
        emit ProbabilitySet(eventA, eventB, value);
    }

    /// VIEW — lettura probabilità
    function getProbability(
        uint256 eventA,
        uint256 eventB
    )
        external
        view
        returns (uint32)
    {
        return probabilities[eventA][eventB];
    }
}
