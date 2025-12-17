import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("OrdineModule", (m) => {
  const ordine = m.contract("Ordine");

  return { ordine };
});
