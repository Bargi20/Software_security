import { ethers } from "ethers";
import * as dotenv from "dotenv";
import { artifacts } from "hardhat";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  // Cartella dei contratti
  const contractsDir = path.join(__dirname, "..", "contracts");
  const contractFiles = fs.readdirSync(contractsDir).filter(f => f.endsWith(".sol"));

  if (contractFiles.length === 0) throw new Error("Nessun file .sol trovato nella cartella contracts");

  const rpcUrl = process.env.BESU_RPC_URL;
  const privateKeys = process.env.BESU_PRIVATE_KEYS
    ? JSON.parse(process.env.BESU_PRIVATE_KEYS)
    : [];

  if (!rpcUrl || privateKeys.length === 0) throw new Error("Configura BESU_RPC_URL e BESU_PRIVATE_KEYS nel .env");

  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const wallet = new ethers.Wallet(privateKeys[0], provider);

  // Cartella deploy
  const deployDir = path.join(__dirname, "..", "ignition", "deployments", "chain-1338");
  if (!fs.existsSync(deployDir)) fs.mkdirSync(deployDir, { recursive: true });

  for (const contractFile of contractFiles) {
    const contractName = path.parse(contractFile).name;
    console.log(`\nDeployando contratto: ${contractName}`);

    // Leggi artifact
    const artifact = await artifacts.readArtifact(contractName);

    // ContractFactory
    const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, wallet);

    // Deploy
    const contract = await factory.deploy();

    // Attendi conferma
    const tx = contract.deploymentTransaction();
    if (!tx) throw new Error("Transazione di deploy non trovata");
    await tx.wait();

    console.log(`${contractName} deployato all'indirizzo:`, contract.target);

    // Salva ABI
    const abiPath = path.join(deployDir, `${contractName}_abi.json`);
    fs.writeFileSync(abiPath, JSON.stringify(artifact.abi, null, 2));
    //console.log("ABI salvata in:", abiPath);

    // Salva indirizzo in un file separato per ogni contratto
    const addrPath = path.join(deployDir, `${contractName}_address.json`);
    fs.writeFileSync(addrPath, JSON.stringify({ [contractName]: contract.target }, null, 2));
    //console.log("Indirizzo salvato in:", addrPath);
  }
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
