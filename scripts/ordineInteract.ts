import { ethers } from "ethers";
import * as dotenv from "dotenv";
import { artifacts } from "hardhat";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

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

  const artifact = await artifacts.readArtifact("Ordine");
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const filePath = path.join(__dirname, "..", "ignition", "deployments", "chain-1338", "deployed_addresses.json");

  const deployedAddresses = JSON.parse(fs.readFileSync(filePath, "utf8"));
  //console.log("Artifact:", artifact.abi);
  //console.log("Deployed Addresses:", deployedAddresses["OrdineModule#Ordine"]);
  //console.log("Wallet Address:", wallet.address);

const contract = new ethers.Contract(deployedAddresses["OrdineModule#Ordine"], artifact.abi, wallet);

await contract.creaOrdine("1", "indirizzo", "Mario", "Rossi", "citofono");

console.log(await contract.getOrdine("1")); 
}


main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
