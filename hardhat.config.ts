import type { HardhatUserConfig } from "hardhat/config";
import hardhatToolboxViemPlugin from "@nomicfoundation/hardhat-toolbox-viem";
import dotenv from "dotenv";
dotenv.config({ path: 'app/.env' });

const BESU_RPC_URL = process.env.BESU_RPC_URL;
const BESU_PRIVATE_KEYS = process.env.BESU_PRIVATE_KEYS ? JSON.parse(process.env.BESU_PRIVATE_KEYS) : [];

const config: HardhatUserConfig = {
  plugins: [hardhatToolboxViemPlugin],
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
      },
    ],
  },
  networks: {
    ganache: {
      type: "http",
      url: "http://localhost:7545",
      chainId: 1337,
      gas: 6000000,
      gasPrice: 20000000000
    },
    besu: {
      type: "http",
      url: BESU_RPC_URL!,
      chainId: 1338,
      accounts: BESU_PRIVATE_KEYS,
      gas: 4000000,
      gasPrice: 0
    }
  }
};

export default config;
