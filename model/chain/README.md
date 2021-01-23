# Chain-based modeling

To model ESD system behavior, you can run it on a local blockchain using the
Truffle project in this directory.

This is challenging because the EDS system contracts all want to read from
Constants.sol, and the Mock versions sometimes want constructor arguments, and
the Deployers that set up the system don't have access to their own state when
operating on the system state.

First, you need to install the dependencies in this directory:

```
npm install
```

Then, you need Ganache running. Note that you may need to `npm install -g` it first. You also need to raise its default gas limit.

```
ganache-cli -p 7545 --gasLimit 8000000
```

Then, you can deploy into Ganache with Truffle (which you also may need to `npm install -g`).

```
truffle migrate --network=development
```

Then, you can run a model against the chain.

TODO: Implement something with pyweb3 that can share agents and action representations with integrated Python version?




