import { ethers } from "ethers";
import fs from "fs"; //serve per interagire con i file "posizionali" (JSON)

// Spostarsi sul Desktop da WSL2 Ubuntu e poi nella project root
// /mnt/c/Users/barca/Desktop

// digita dal terminale di Ubuntu WSL2 nella cartella "quorum-test-network" se:
// 1) ./stop.sh --> vuoi interrompere la rete
// 2) ./run.sh --> primo setup rete e nodi
// 3) ./resume.sh --> per riprendere la rete
// 4) rm .quorumDevQuickstart.lock --> per qualsiasi problema della rete; poi ri-digita ./run.sh per reinstallare rete

//SOLO PER PRIMA INSTALLAZIONE DALLA CARTELLA 

async function main() {
  const provider = new ethers.JsonRpcProvider("http://localhost:8545"); // sempre questo è
  //console.log(provider);
  const signer = new ethers.Wallet("0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63", provider); //chiave privata account MetaMask

  //const address = JSON.parse(fs.readFileSync("ignition/deployments/chain-31337/deployed_addresses.json", "utf8"));
  const abi = JSON.parse(fs.readFileSync("artifacts/contracts/Helloethereum.sol/HelloEthereum.json", "utf8"));
  //console.log(abi.abi);

  const contract = new ethers.Contract("0x2E1f232a9439C3D459FcEca0BeEf13acc8259Dd8", abi.abi, signer);



  const initialMessage = await contract.message();
  console.log("Messaggio iniziale:", initialMessage);

  // await contract.updateMessage("test4");

  // const updatedMessage = await contract.message();
  // console.log("Messaggio aggiornato:", updatedMessage);

}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});