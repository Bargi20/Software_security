import { ethers } from "ethers";
import { artifacts } from "hardhat";

async function main() {
  const provider = new ethers.JsonRpcProvider("http://localhost:8545"); // sempre questo è
  const signer = new ethers.Wallet("0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63", provider); //chiave privata account MetaMask

  const artifact = await artifacts.readArtifact("HelloEthereum");
  const contract = new ethers.Contract("0x42699A7612A82f1d9C36148af9C77354759b210b", artifact.abi, signer);

  const initialMessage = await contract.message();
  console.log("Messaggio iniziale:", initialMessage);

  const tx = await contract.updateMessage("test6");
  await tx.wait();
  
  const updatedMessage = await contract.message();
  console.log("Messaggio aggiornato:", updatedMessage);

}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});