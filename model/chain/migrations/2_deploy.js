const MockDeployer1 = artifacts.require("MockDeployer1");
const MockDeployer2 = artifacts.require("MockDeployer2");
const MockDeployer3 = artifacts.require("MockDeployer3");
const MockOracle = artifacts.require("MockOracle");
const MockPool = artifacts.require("MockPool");
const Implementation = artifacts.require("Implementation");
const Root = artifacts.require("Root");
const TestnetUSDC = artifacts.require("TestnetUSDC");

const UniswapV2FactoryBytecode = require('@uniswap/v2-core/build/UniswapV2Factory.json').bytecode


async function deployTestnetUSDC(deployer) {
  return await deployer.deploy(TestnetUSDC);
}

async function deployTestnet(deployer, network, accounts) {
  console.log('Deploy fake USDC');
  const usdc = await deployTestnetUSDC(deployer);

  console.log('Deploy MockDeployer1');
  const d1 = await deployer.deploy(MockDeployer1);
  console.log('Deploy Root');
  const root = await deployer.deploy(Root, d1.address);
  console.log('View Root as MockDeployer1');
  const rootAsD1 = await MockDeployer1.at(root.address);

  console.log('Deploy fake Uniswap Factory');
  // We need an address arg to the contract
  let uniswapArg = '';
  for (let i = 0; i < 32; i++) {
    uniswapArg += '00';
  }
  const uniswapFactoryAddress = (await web3.eth.sendTransaction({from: accounts[0], gas: 8000000, data: UniswapV2FactoryBytecode + uniswapArg})).contractAddress;
  
  console.log('Deploy MockDeployer2');
  const d2 = await deployer.deploy(MockDeployer2);
  console.log('Implement MockDeployer2');
  await rootAsD1.implement(d2.address);
  console.log('View root as MockDeployer2');
  const rootAsD2 = await MockDeployer2.at(root.address);
  
  // Set up the fields of the oracle that we can't pass through a Deployer
  const oracleAddress = await rootAsD2.oracle.call();
  const oracle = await MockOracle.at(oracleAddress);
  console.log('MockOracle is at: ' + oracleAddress);
  
  // Make the oracle make the Uniswap pair on our custom factory
  await oracle.set(uniswapFactoryAddress, usdc.address);
  const pair = await oracle.pair.call();
  console.log('Uniswap pair is at: ' + pair);

  console.log('Deploy MockDeployer3');
  const d3 = await deployer.deploy(MockDeployer3);
  console.log('Implement MockDeployer3');
  await rootAsD2.implement(d3.address);
  console.log('View root as MockDeployer3');
  const rootAsD3 = await MockDeployer3.at(root.address);
  
  // Set up the fields of the pool that we can't pass through a Deployer
  const pool = await MockPool.at(await rootAsD3.pool.call())
  console.log('MockPool is at: ' + pool.address)
  await pool.set(rootAsD3.address, await rootAsD3.dollar.call(), pair);

  console.log('Deploy current Implementation');
  const implementation = await deployer.deploy(Implementation);
  console.log('Implement current Implementation');
  await rootAsD3.implement(implementation.address);
}

module.exports = function(deployer, network, accounts) {
  deployer.then(async() => {
    console.log(deployer.network);
    switch (deployer.network) {
      case 'development':
        await deployTestnet(deployer, network, accounts);
        break;
      default:
        throw("Unsupported network");
    }
  })
};

