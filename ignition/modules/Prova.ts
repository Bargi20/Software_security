import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("ParityCheckerModule", (m) => {
  const ParityChecker = m.contract("ParityChecker");
  return { ParityChecker };
});