import { ethers } from "ethers";
import fs from "fs";

async function main() {
  const provider = new ethers.JsonRpcProvider("http://localhost:8545"); // sempre questo è
  //console.log(provider);
  const signer = new ethers.Wallet("0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63", provider); //chiave privata account MetaMask

  const contractJson = JSON.parse(fs.readFileSync("artifacts/contracts/test.sol/ParityChecker.json", "utf8"));
  const abi = contractJson.abi;
  const bytecode = contractJson.bytecode;

  //console.log(abi, bytecode)

  
  //const balance = await provider.getBalance(signer.address);
  //console.log(balance.toString())
  

  const factory = new ethers.ContractFactory(abi, bytecode, signer);

  //console.log(factory);
  //const balance = await provider.getBalance('0xe49010FBd5Ed4346349a5eD8fA2852D1a210A1ec');
  //console.log(balance.toString());
  
  
  const contract = await factory.deploy("ciao", { gasLimit: 600_000});
  console.log("Contratto deployato all'indirizzo:", await contract.getAddress());

 }

main().catch((error) => {
  console.error(error);
  //process.exit(1);
});
