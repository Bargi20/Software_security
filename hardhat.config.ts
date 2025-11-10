import type { HardhatUserConfig } from "hardhat/config";

import hardhatToolboxViemPlugin from "@nomicfoundation/hardhat-toolbox-viem";
import { configVariable } from "hardhat/config";
import hardhatEthers from "@nomicfoundation/hardhat-ethers";

const config: HardhatUserConfig = {
  plugins: [hardhatToolboxViemPlugin, hardhatEthers],
  solidity: {
    compilers: [
      {
        version: "0.8.19",
        settings: {
          optimizer: {
            enabled: true,
            runs: 200,
          },
        },
      }
    ]
  },
  networks: {
    hardhatMainnet: {
      type: "edr-simulated",
      chainType: "l1",
    },
    hardhatOp: {
      type: "edr-simulated",
      chainType: "op",
    },
    sepolia: {
      type: "http",
      chainType: "l1",
      url: configVariable("SEPOLIA_RPC_URL"),
      accounts: [configVariable("SEPOLIA_PRIVATE_KEY")],
    },
    besu_node1: {
      type: "http",
      url: "http://localhost:8545", // Node 1
      chainId: 1337,
      accounts: [
        "0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63"
      ],
      gas: 6000000,
      gasPrice: 20000000000
    },
    besu_node2: {
      type: "http",
      url: "http://localhost:8547", // Node 2
      chainId: 1337,
      accounts: [
        "0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63"
      ],
      gas: 6000000,
      gasPrice: 20000000000
    },
    besu_node3: {
      type: "http",
      url: "http://localhost:8549", // Node 3
      chainId: 1337,
      accounts: [
        "0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63"
      ],
      gas: 6000000,
      gasPrice: 20000000000
    },
    besu_node4: {
      type: "http",
      url: "http://localhost:8551", // Node 4
      chainId: 1337,
      accounts: [
        "0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63"
      ],
      gas: 6000000,
      gasPrice: 20000000000
    },
    // Alias per compatibilità
    besu: {
      type: "http",
      url: "http://localhost:8545", // Default al Node 1
      chainId: 1337,
      accounts: [
        "0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63"
      ],
      gas: 6000000,
      gasPrice: 20000000000
    }
  },
};

export default config;
