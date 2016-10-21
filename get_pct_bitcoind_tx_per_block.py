"""Given a starting block height, print estimated pct of bitcoind transactions.

Usage:
    python get_pct_bitcoind_tx_per_block.py starting-block-height-int
"""
import sys
import blockchain_reader #blockchain_reader.py

def _main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python get_pct_bitcoind_tx_per_block.py "
                 "starting-block-height-int")
    block_height = int(sys.argv[1])

    total_txs = 0
    total_bitcoind_txs = 0

    try:
        while True:
            block = blockchain_reader.Block(block_height)
            pct = block.get_pct_core_tx() * 100.0
            total_txs += block.get_num_tx()
            total_bitcoind_txs += block.get_num_bitcoind_tx()
            total_pct = total_bitcoind_txs * 100.0 / total_txs
            print("Block %d: %.2f%% (%.2f%% so far)" %
                  (block_height, pct, total_pct))
            block_height += 1

    except KeyboardInterrupt:
        sys.exit("Ok ok, quitting")

if __name__ == '__main__':
    _main()
