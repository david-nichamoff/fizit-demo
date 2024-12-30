/**
 * Use this file to configure your truffle project. It's seeded with some
 * common settings for different networks and features like migrations,
 * compilation, and testing. Uncomment the ones you need or modify
 * them to suit your project as necessary.
 *
 * More information about configuration can be found at:
 *
 * https://trufflesuite.com/docs/truffle/reference/configuration
 *
 * Hands-off deployment with Infura
 * --------------------------------
 *
 * Do you have a complex application that requires lots of transactions to deploy?
 * Use this approach to make deployment a breeze 🏖️:
 *
 * Infura deployment needs a wallet provider (like @truffle/hdwallet-provider)
 * to sign transactions before they're sent to a remote public node.
 * Infura accounts are available for free at 🔍: https://infura.io/register
 *
 * You'll need a mnemonic - the twelve word phrase the wallet uses to generate
 * public/private key pairs. You can store your secrets 🤐 in a .env file.
 * In your project root, run `$ npm install dotenv`.
 * Create .env (which should be .gitignored) and declare your MNEMONIC
 * and Infura PROJECT_ID variables inside.
 * For example, your .env file will have the following structure:
 *
 * MNEMONIC = <Your 12 phrase mnemonic>
 * PROJECT_ID = <Your Infura project id>
 *
 * Deployment with Truffle Dashboard (Recommended for best security practice)
 * --------------------------------------------------------------------------
 *
 * Are you concerned about security and minimizing rekt status 🤔?
 * Use this method for best security:
 *
 * Truffle Dashboard lets you review transactions in detail, and leverages
 * MetaMask for signing, so there's no need to copy-paste your mnemonic.
 * More details can be found at 🔎:
 *
 * https://trufflesuite.com/docs/truffle/getting-started/using-the-truffle-dashboard/
 */

// require('dotenv').config();
// const { MNEMONIC, PROJECT_ID } = process.env;
// const privateKey = ['0x198923fbb16af47b7647b442c790eb3fc53a9c6092e00f70a2893dc08348f609']; // Private key as an array of one element
// const desiredWalletAddress = '0xf0F2442f2B8541EFcd4235b2933Bd7b2098bCA0c';
// const HDWalletProvider = require('@truffle/hdwallet-provider');

const CubeSignerProvider = require('./signer');

module.exports = {
  networks: {
    avalanchePrivate: {
      provider: () => new CubeSignerProvider(
        'https://subnets.avacloud.io/d3cba7f9-84c5-4bdd-a708-c5691bf9dee4', 
        '0xe5aCE1cFcA647b064ca12Fd5Fc32eBaD6e7b4c53'
      ),
      provider: () => new HDWalletProvider(privateKey, customRPCUrl),
      network_id: '1147321', // Network ID for Avalanche
      gas: 0, // Adjust gas limit as needed
      gasPrice: 0, // Adjust gas price as needed
      timeoutBlocks: 200,
      skipDryRun: true
    }
  },
  compilers: {
    solc: {
      version: "0.8.0", // Specify compiler version
      settings: {
        optimizer: {
          enabled: true,
          runs: 200
        },
      }
    }
  }
};
