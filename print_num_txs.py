"""Given a starting block height, print # of transactions per block.

Usage:
    python print_num_txs.py starting-block-height-int [end-block-height-int]
"""
import sys
import blockchain_reader #blockchain_reader.py


def _main():
    block_height = None
    last_height = None
    if len(sys.argv) not in (2, 3):
        sys.exit("Usage: python print_num_txs.py starting-block-height-int "
                 "[end-block-height-int]")
    else:
        block_height = int(sys.argv[1])

    if len(sys.argv) == 3:
        last_height = int(sys.argv[2])

    try:
        while True:
            block = blockchain_reader.Block(block_height)
            num_txs = block.get_num_tx()
            print "%d" % num_txs
            block_height += 1

            if last_height is not None and block_height > last_height:
                break
        print "Done."

    except KeyboardInterrupt:
        sys.exit("Ok ok, quitting")

if __name__ == '__main__':
    _main()
