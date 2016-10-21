"""Given a starting block height, print estimated pct of bitcoind wallets.

A wallet is considered a bitcoind wallet if one or more transactions has inputs
that matches a designated wallet_id assigned by WalletExplorer.com's API.

Usage:
    python get_pct_bitcoind_wallets_per_block.py starting-block-height-int
"""
import sys
import blockchain_reader #blockchain_reader.py


def _main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python get_pct_bitcoind_wallets_per_block.py "
                 "starting-block-height-int")
    block_height = int(sys.argv[1])

    try:
        while True:
            block = blockchain_reader.Block(block_height)
            pct = block.get_pct_bitcoind_wallets() * 100.0
            num_wallets = block.get_num_wallets()
            num_bitcoind_wallets = block.get_num_bitcoind_wallets()

            print("Block %d: %.2f%% %d %d" %
                  (block_height, pct, num_wallets, num_bitcoind_wallets))
            block_height += 1

    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == '__main__':
    _main()
