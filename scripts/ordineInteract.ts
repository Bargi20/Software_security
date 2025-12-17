import { ethers } from "ethers";
import * as dotenv from "dotenv";


dotenv.config();

const rpcUrl = process.env.BESU_RPC_URL;
const privateKeys: string[] = process.env.BESU_PRIVATE_KEYS
  ? JSON.parse(process.env.BESU_PRIVATE_KEYS)
  : [];

async function main() {
  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const wallet = new ethers.Wallet(
    "0x" + privateKeys[0], //prende la prima chiave privata nell'env
    provider
  );

  


  console.log("Wallet address:", wallet.address);




}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
