import { ethers } from "ethers";
import { artifacts } from "hardhat";

async function main() {
  // Connessione al provider
  const provider = new ethers.JsonRpcProvider("http://localhost:8545");
  
  // Usa la private key dall'hardhat.config.ts
  const privateKey = "0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63";
  const signer = new ethers.Wallet(privateKey, provider);
  
  const address0 = await signer.getAddress();
  console.log("Signer address:", address0);
  
  // Leggiamo l'ABI del contratto
  const contractArtifact = await artifacts.readArtifact("ParityChecker");
  
  // Deploy del contratto
  const contractFact = new ethers.ContractFactory(contractArtifact.abi, contractArtifact.bytecode, signer);
  const contract = await contractFact.deploy();
  
  await contract.waitForDeployment();
  
  console.log("Contract deployed at:", await contract.getAddress());
  
  // Cast a any per chiamare le funzioni
  const parityChecker = contract as any;
  
  // Test delle funzioni del ParityChecker
  console.log("Testing isEven(10):", await parityChecker.isEven(10));
  console.log("Testing isEven(7):", await parityChecker.isEven(7));
  console.log("Testing stampaMess('Ciao!'):", await parityChecker.stampaMess("Ciao!"));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});