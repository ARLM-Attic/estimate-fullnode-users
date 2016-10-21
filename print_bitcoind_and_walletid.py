"""From starting height, print whether txs are bitcoind and their wallet id.

Usage:
    python print_bitcoind_and_walletid.py starting-block-height-int
"""
import sys
import blockchain_reader #blockchain_reader.py


def _main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python print_bitcoind_and_walletid.py "
                 "starting-block-height-int")
    block_height = int(sys.argv[1])

    try:
        while True:
            block = blockchain_reader.Block(block_height)
            api_reader = blockchain_reader.WalletExplorerReader()
            tx_ids = block.get_txids()
            for txid in tx_ids:
                tx_json = block.rpc_reader.get_decoded_tx(txid)
                if ('coinbase' in tx_json['vin'][0]):
                    continue #skip coinbase txs
                is_bitcoind = blockchain_reader.is_bitcoind_tx(
                    tx_json, block.rpc_reader)
                wallet_id = api_reader.get_wallet_id(txid)
                print "%s %s %s" % (txid, str(is_bitcoind), wallet_id)
            block_height += 1

    except KeyboardInterrupt:
        sys.exit("Ok ok, quitting")

if __name__ == '__main__':
    _main()
