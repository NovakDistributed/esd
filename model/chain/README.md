# Chain-based modeling

To model ESD system behavior, you can run it on a local blockchain using the Truffle project in this directory.

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


