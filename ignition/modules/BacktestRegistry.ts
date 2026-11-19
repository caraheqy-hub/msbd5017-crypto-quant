
import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

export default buildModule("BacktestRegistryModule", (m) => {
  const registry = m.contract("BacktestRegistry");

  return { registry };
});
