import { ethers } from "ethers";
import { artifacts } from "hardhat";
import * as readline from 'readline';

// Interfaccia per input utente
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function askQuestion(question: string): Promise<string> {
  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      resolve(answer);
    });
  });
}

async function main() {
  console.log("🎮 ParityChecker Interactive Console");
  console.log("=====================================\n");
  
  // Setup provider e signer
  const provider = new ethers.JsonRpcProvider("http://localhost:8545");
  const privateKey = "0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63";
  const signer = new ethers.Wallet(privateKey, provider);
  
  console.log("👤 Usando account:", await signer.getAddress());
  
  // Opzione 1: Deploy nuovo contratto o connetti a esistente
  const choice = await askQuestion("Vuoi:\n1) Deployare nuovo contratto\n2) Connetterti a contratto esistente\nScegli (1 o 2): ");
  
  let contract: any;
  
  if (choice === "1") {
    // Deploy nuovo contratto
    console.log("\n🚀 Deploying nuovo ParityChecker...");
    
    // Leggi ABI e bytecode
    const contractArtifact = await artifacts.readArtifact("ParityChecker");
    const contractFactory = new ethers.ContractFactory(
      contractArtifact.abi, 
      contractArtifact.bytecode, 
      signer
    );
    
    contract = await contractFactory.deploy();
    await contract.waitForDeployment();
    
    console.log("✅ Contract deployed to:", await contract.getAddress());
    
  } else if (choice === "2") {
    // Connetti a contratto esistente
    const address = await askQuestion("\n📍 Inserisci l'indirizzo del contratto: ");
    
    try {
      const contractArtifact = await artifacts.readArtifact("ParityChecker");
      contract = new ethers.Contract(address, contractArtifact.abi, signer);
      console.log("✅ Connesso al contratto:", address);
    } catch (error) {
      console.error("❌ Errore nella connessione:", error);
      rl.close();
      return;
    }
  } else {
    console.log("❌ Scelta non valida");
    rl.close();
    return;
  }
  
  // Menu interattivo
  while (true) {
    console.log("\n🔧 Cosa vuoi fare?");
    console.log("1) Controlla se un numero è pari o dispari");
    console.log("2) Invia un messaggio");
    console.log("3) Test automatico");
    console.log("4) Mostra info contratto");
    console.log("5) Esci");
    
    const action = await askQuestion("Scegli un'opzione (1-5): ");
    
    try {
      switch (action) {
        case "1":
          await checkParity(contract);
          break;
        case "2":
          await sendMessage(contract);
          break;
        case "3":
          await automaticTest(contract);
          break;
        case "4":
          await showContractInfo(contract, provider);
          break;
        case "5":
          console.log("👋 Arrivederci!");
          rl.close();
          return;
        default:
          console.log("❌ Opzione non valida");
      }
    } catch (error) {
      console.error("❌ Errore:", error);
    }
  }
}

async function checkParity(contract: any) {
  const numberStr = await askQuestion("\n🔢 Inserisci un numero: ");
  const number = parseInt(numberStr);
  
  if (isNaN(number)) {
    console.log("❌ Devi inserire un numero valido");
    return;
  }
  
  console.log(`\n⏳ Controllando se ${number} è pari o dispari...`);
  const result = await contract.isEven(number);
  console.log(`✅ Risultato: ${number} è ${result}`);
}

async function sendMessage(contract: any) {
  const message = await askQuestion("\n💬 Inserisci il tuo messaggio: ");
  
  console.log(`\n⏳ Inviando messaggio: "${message}"...`);
  const result = await contract.stampaMess(message);
  console.log(`✅ Messaggio ricevuto dal contratto: "${result}"`);
}

async function automaticTest(contract: any) {
  console.log("\n🔄 Eseguendo test automatico...\n");
  
  // Test numeri pari e dispari
  const numbers = [0, 1, 2, 7, 10, 42, 99, 100];
  console.log("📊 Test funzione isEven:");
  for (const num of numbers) {
    const result = await contract.isEven(num);
    console.log(`  ${num} → ${result}`);
  }
  
  // Test messaggi
  console.log("\n📨 Test funzione stampaMess:");
  const messages = [
    "Hello Blockchain!",
    "Besu funziona perfettamente",
    "Test di smart contract",
    "🎉 Successo!"
  ];
  
  for (const msg of messages) {
    const result = await contract.stampaMess(msg);
    console.log(`  "${msg}" → "${result}"`);
  }
  
  console.log("\n✅ Test completato!");
}

async function showContractInfo(contract: any, provider: ethers.JsonRpcProvider) {
  console.log("\n📋 Informazioni Contratto:");
  console.log("========================");
  
  const address = await contract.getAddress();
  console.log(`📍 Indirizzo: ${address}`);
  
  // Ottieni info sulla rete
  const network = await provider.getNetwork();
  console.log(`🌐 Network: ${network.name} (Chain ID: ${network.chainId})`);
  
  // Ottieni numero blocco corrente
  const blockNumber = await provider.getBlockNumber();
  console.log(`📦 Blocco corrente: ${blockNumber}`);
  
  // Funzioni disponibili
  console.log(`🔧 Funzioni disponibili:`);
  console.log(`  - isEven(uint number) → string`);
  console.log(`  - stampaMess(string message) → string`);
}

main().catch((error) => {
  console.error("❌ Errore fatale:", error);
  rl.close();
  process.exit(1);
});