import { network } from "hardhat";
import { ethers } from "ethers";

async function main() {
  console.log("🔍 Testing Besu connection...");
  const provider = new ethers.JsonRpcProvider("http://localhost:8545");
  const signer = await provider.getSigner(0);
  console.log("📝 Account:", await signer.getAddress());
  
  // Verifica che il provider non sia null
  if (!signer.provider) {
    throw new Error("Provider is null");
  }
  
  const balance = await signer.provider.getBalance(signer.address);
  console.log("💰 Balance:", ethers.formatEther(balance), "ETH");
  
  const blockNumber = await signer.provider.getBlockNumber();
  console.log("📦 Current block:", blockNumber);
  
  const network = await signer.provider.getNetwork();
  console.log("🌐 Chain ID:", network.chainId);
  
  console.log("✅ Besu connection successful!");
}

main().catch(console.error);