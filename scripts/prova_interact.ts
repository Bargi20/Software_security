import { network } from "hardhat";
const { ethers } = await network.connect();

async function saldo(){
    // Print dell'indirizzo del deployer ed del suo saldo
    const [deployer, otherAccount] = await ethers.getSigners();
    ethers.formatEther(await ethers.provider.getBalance(deployer));
    console.log("\nIl mio indirizzo:", deployer.address);
    const balance = await ethers.provider.getBalance(deployer.address);
    console.log("Saldo:", ethers.formatEther(balance), "ETH");
  }

async function main() {
  // Recupera il factory del contratto
  const Prova = await ethers.getContractFactory("ParityChecker");

  // Deploy del contratto
  const contract = await Prova.deploy();
  const deploytx = await contract.getAddress();
  console.log("Contratto", await contract.name ,"deployed to:", deploytx, '\n');

  // Ci attacchiamo all'istanza deployata per interagire
  const contractDeployed = await Prova.attach(deploytx);

  // Chiama la funzione isEven
  const param = 7;
  const result = await contractDeployed.isEven(param);
  console.log(param, "è:", result, "\n");

  // Chiama la funzione stampaMess
  const messaggio = "Appottooo";
  console.log("Messaggio: ", await contractDeployed.stampaMess(messaggio));
  saldo();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});