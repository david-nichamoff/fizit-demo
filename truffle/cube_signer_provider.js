const HDWalletProvider = require("@truffle/hdwallet-provider");
const { spawnSync } = require("child_process");
const fs = require("fs");

/**
 * Fetch secrets from SecretsManager.py.
 * @returns {Object} - The secrets dictionary.
 */
function getSecrets() {
  try {
    const scriptPath = "./path/to/SecretsManager.py";
    const result = spawnSync("python", [scriptPath], { encoding: "utf-8" });

    if (result.error) {
      throw new Error(`Error executing SecretsManager.py: ${result.error.message}`);
    }

    if (result.stderr) {
      throw new Error(`SecretsManager.py returned an error: ${result.stderr}`);
    }

    return JSON.parse(result.stdout);
  } catch (error) {
    console.error("Error fetching secrets from SecretsManager:", error);
    throw error;
  }
}

/**
 * Initialize CubeSigner Provider with session token and wallet address.
 * @param {Object} options - The configuration options.
 * @param {string} options.rpcUrl - The RPC URL for the network.
 * @param {number} options.chainId - The chain ID for the network.
 * @returns {HDWalletProvider} - An instance of HDWalletProvider.
 */
function CubeSignerProvider({ rpcUrl, chainId }) {
  const secrets = getSecrets();

  const sessionToken = secrets["role_session_token"];
  const contractWallet = secrets["contract_wallet_address"];
  const privateKey = secrets["private_key"]; // Fallback if required

  if (!sessionToken || !contractWallet) {
    throw new Error(
      "Required secrets ('role_session_token' or 'contract_wallet_address') are missing."
    );
  }

  console.log(`Using CubeSigner session token from SecretsManager.`);
  console.log(`Contract Wallet: ${contractWallet}`);

  // Initialize the provider using the RPC URL and private key (if needed)
  return new HDWalletProvider({
    privateKeys: [privateKey], // Replace this logic with CubeSigner if privateKey is not used
    providerOrUrl: rpcUrl,
  });
}

module.exports = CubeSignerProvider;