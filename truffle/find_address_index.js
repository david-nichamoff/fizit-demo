const HDWalletProvider = require('@truffle/hdwallet-provider');
const mnemonic = 'night bar acoustic library lunch fluid maze display midnight scatter check glad before right foster best sea define general minor clog found chronic head'
const customRPCUrl = 'https://subnets.avacloud.io/f8b4d7c7-e374-4d79-abdd-e2e3ba007481';
const targetWalletAddress = '0xf0F2442f2B8541EFcd4235b2933Bd7b2098bCA0c';

async function findAddressIndex() {
  const provider = new HDWalletProvider({
    mnemonic: { phrase: mnemonic },
    providerOrUrl: customRPCUrl
  });

  let addressIndex = 0;
  let walletAddress;

  try {
    // Attempt to retrieve wallet addresses until a match is found or limit is reached
    while (addressIndex < 1000) {
      walletAddress = await provider.getAddress(addressIndex);

      if (walletAddress && walletAddress.toLowerCase() === targetWalletAddress.toLowerCase()) {
        console.log(`Found addressIndex ${addressIndex} for wallet address ${targetWalletAddress}`);
        return addressIndex;
      }

      addressIndex++;
    }

    console.log(`Address index not found for wallet address ${targetWalletAddress}`);
    return null;
  } catch (error) {
    console.error(`Error while retrieving address: ${error.message}`);
    return null;
  } finally {
    provider.engine.stop(); // Stop the provider to release resources
  }
}

// Call the function to find the addressIndex
findAddressIndex().then(() => {
  process.exit(0); // Exit the Node.js process after completion
}).catch(err => {
  console.error(err);
  process.exit(1); // Exit with an error if there's a problem
});
