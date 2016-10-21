# estimate-fullnode-users

Use bitcoind and simple heuristics to estimate the number of fullnode users

## Usage

    $ python get_pct_bitcoind_wallets_per_block.py starting-block-height-int

## Requirements

* [bitcoinrpc](https://github.com/jgarzik/python-bitcoinrpc) `[sudo] python setup.py install`
* Python 2

## Configuration

You will need to create a config file to connect to bitcoind's RPC interface for blockchain data, and walletexplorer.com's API for clustering analysis.

project.cfg:
```
username=xxxxx
password=xxxxx
host=127.0.0.1
port=8332
api_key=xxxxxx
```
Go to [walletexplorer.com](https://www.walletexplorer.com/) for an API key.

You will need the following entries at a minimum in your `bitcoin.conf` file if you choose to use bitcoind rather than remote API.

```ini
# server=1 tells Bitcoin-QT to accept JSON-RPC commands.
server=1

# You must set rpcuser and rpcpassword to secure the JSON-RPC api
rpcuser=my_fabulous_username_CHANGEME
rpcpassword=my_secret_password_CHANGEME

# Listen for RPC connections on this TCP port:
rpcport=8332

#Maintain a full transaction index, used by the getrawtransaction rpc call (default: 0)
txindex=1
```

## Heuristics

### locktime

 * PR: https://github.com/bitcoin/bitcoin/pull/2340/files: `txNew.nLockTime = std::max(0, chainActive.Height() - 10);`
 * Introduced in 0.11.0 [release notes](https://bitcoincore.org/en/releases/0.11.0/) [July 10, 2015](https://github.com/bitcoin/bitcoin/releases/tag/v0.11.0) circa block height [364700](https://blockchain.info/block-height/364700)

### sequence number

 * Value: 4294967294
 * Same PR for locktime useful for reference

### P2PKH addresses

* All inputs must be P2PKH spends

## Author

[@kristovatlas](https://github.com/kristovatlas)
