"""Given a starting block height, print all locktime and sequence values.

Usage:
    python print_sequence_and_nlocktime.py starting-block-height-int
"""
import sys
import blockchain_reader #blockchain_reader.py


def _main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python print_sequence_and_nlocktime.py "
                 "starting-block-height-int")
    block_height = int(sys.argv[1])

    try:
        while True:
            block = blockchain_reader.Block(block_height)
            txs = block.get_tx_id_locktime_seq()
            for txid, locktime, seq in txs:
                print "%s %s %s" % (txid, locktime, seq)
            block_height += 1

    except KeyboardInterrupt:
        sys.exit("Ok ok, quitting")

if __name__ == '__main__':
    _main()
