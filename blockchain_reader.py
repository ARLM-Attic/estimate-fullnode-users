"""Use bitcoind RPC interface to gather blockchain data."""

import json
from bitcoinrpc.authproxy import AuthServiceProxy #dependency
import http #http.py
import stdout_io #stdout_io.py

CFG_FILENAME = 'project.cfg'

def is_bitcoind_tx(tx_json, rpc_reader):
    """Examines a transaction to determine if it is likely a bitcoind tx.

    Heuristics:
        * The locktime value is between 364700 and 500000
        * All vins have a sequence value of 4294967294
        * All vins have an address that begins with '1' instead of '3'
    """
    assert isinstance(tx_json, dict)
    locktime = int(tx_json['locktime'])
    if locktime < 364700 or locktime > 500000:
        return False
    for vin in tx_json['vin']:
        if vin['sequence'] != 4294967294:
            return False
        prev_tx_id = vin['txid']
        prev_tx_vout = int(vin['vout'])
        prev_tx_json = rpc_reader.get_decoded_tx(prev_tx_id)
        input_addresses = (prev_tx_json['vout'][prev_tx_vout]['scriptPubKey']
                           ['addresses'])
        for address in input_addresses:
            if address.startswith('3'):
                return False
    return True


def get_config_settings():
    """Get settings from default config file.
    File format:
    username=xxxx
    password=xxxx
    host=somehost
    port=123
    api_key=xxxx

    Returns: [username (str), password (str), host (str), port (str),
              api_key (str)]
    """
    username, password, host, port, api_key = (None,)*5
    with open(CFG_FILENAME, 'r') as cfg:
        for line in cfg.readlines():
            line = line.rstrip()
            if '=' in line:
                pieces = line.split('=')
                if len(pieces) != 2:
                    raise ValueError("Invalid config file format.")
                if pieces[0] == 'username':
                    username = pieces[1]
                elif pieces[0] == 'password':
                    password = pieces[1]
                elif pieces[0] == 'host':
                    host = pieces[1]
                elif pieces[0] == 'port':
                    port = pieces[1]
                elif pieces[0] == 'api_key':
                    api_key = pieces[1]
                else:
                    raise ValueError("Invalid config file format.")

    if None in (username, password, host, port):
        raise ValueError("Missing configuration in config file.")
    return [username, password, host, port, api_key]


def get_tx_wallet_info_url(tx_id, api_key):
    """General URL to fetch wallet data for specified tx from API."""
    return ("https://www.walletexplorer.com/api/1/tx?txid=%s&caller=%s" %
            (tx_id, api_key))


class NoDataAvailableForGenesisBlockError(Exception):
    """bitcoind has no data for the geneisis block."""
    pass


class NoWalletIDForCoinbaseTransaction(Exception):
    """Coinbase transactions have no wallet id."""
    pass


class Block(object):
    """Data accessor class for a block at specified height."""
    def __init__(self, height):
        """Fetch JSON data for the block at specified height."""
        self.height = height
        self.rpc_reader = LocalBlockchainRPCReader()
        self.hash = self.rpc_reader.get_block_hash_at_height(height)
        self.json = self.rpc_reader.get_json_for_block_hash(self.hash)
        self.num_txs = len(self.json['tx'])
        self.num_bitcoind_txs = None
        self.pct_bitcoind_txs = None
        self.num_wallets = None
        self.num_bitcoind_wallets = None

        #only connect to API if needed
        self.api_reader = None


    def init_api(self):
        """Initialize connection to API if not yet created."""
        if self.api_reader is None:
            self.api_reader = WalletExplorerReader()


    def get_tx_id_locktime_seq(self):
        """Return a list of 3-tuples of [txid, locktime, sequence]"""
        tuple_list = []
        for txid in self.json['tx']:
            tx_json = self.rpc_reader.get_decoded_tx(txid)
            for vin in tx_json['vin']:
                seq = vin['sequence']
                tuple_list.append([txid, tx_json['locktime'], seq])
        return tuple_list


    def get_pct_core_tx(self):
        """Get percentage of txs in block that appear to be bitcoind."""
        if self.pct_bitcoind_txs is not None:
            return self.pct_bitcoind_txs

        if self.num_txs == 0:
            self.num_bitcoind_txs = 0
            self.pct_bitcoind_txs = 0.0
        else:
            bitcoind_txs = 0
            for txid in self.json['tx']:
                tx_json = self.rpc_reader.get_decoded_tx(txid)
                if is_bitcoind_tx(tx_json, self.rpc_reader):
                    bitcoind_txs += 1

            self.num_bitcoind_txs = bitcoind_txs
            self.pct_bitcoind_txs = bitcoind_txs * 1.0 / self.num_txs

        return self.pct_bitcoind_txs


    def get_num_tx(self):
        """Return the int number of txs in this block."""
        return self.num_txs


    def get_num_bitcoind_tx(self):
        """Return the number of estaimted bitcoind transactions."""
        if self.num_bitcoind_txs is None:
            self.get_pct_core_tx()
        return self.num_bitcoind_txs


    def get_txids(self):
        """Return a list of tx hashes in this block."""
        return self.json['tx']


    def get_pct_bitcoind_wallets(self):
        """Out of unique wallets sent from in block, how many are bitcoind?

        Does not include coinbase transaction.
        """
        if None in (self.num_wallets, self.num_bitcoind_wallets):

            self.init_api()

            unique_wallets = set()
            unique_bitcoind_wallets = set()

            pct_done = 0.0
            num_txs = len(self.json['tx'])

            for index, tx_id in enumerate(self.json['tx']):
                pct_done = index * 100.0 / num_txs
                stdout_io.update_stdout("%.2f%%" % pct_done)

                try:
                    wallet_id = self.api_reader.get_wallet_id(tx_id)
                except NoWalletIDForCoinbaseTransaction:
                    continue

                tx_json = self.rpc_reader.get_decoded_tx(tx_id)

                if 'coinbase' in tx_json['vin'][0]:
                    continue #skip coinbase txs

                if is_bitcoind_tx(tx_json, self.rpc_reader):
                    unique_bitcoind_wallets.add(wallet_id)

                #TODO: do we need to check "in" and "add" or faster to just
                #blindly add?
                if wallet_id not in unique_wallets:
                    unique_wallets.add(wallet_id)

            self.num_wallets = len(unique_wallets)
            self.num_bitcoind_wallets = len(unique_bitcoind_wallets)

        try:
            return self.num_bitcoind_wallets * 1.0 / self.num_wallets
        except ZeroDivisionError:
            return 0.0


    def get_num_wallets(self):
        """Return the int number of unique wallets in this block.

        Does not include coinbase transaction.
        """
        if self.num_wallets is None:
            self.get_pct_bitcoind_wallets()
        return self.num_wallets


    def get_num_bitcoind_wallets(self):
        """Return the int number of unique wallets using bitcoind in block.

        Does not include coinbase transaction.
        """
        if self.num_bitcoind_wallets is None:
            self.get_pct_bitcoind_wallets()
        return self.num_bitcoind_wallets


class LocalBlockchainRPCReader(object):
    """Fetches blockchain data from bitcoind RPC interface."""
    def __init__(self, username=None, password=None, host=None,
                 port=None):
        if None in (username, password, host, port):
            username, password, host, port, _ = get_config_settings()
        self.rpc_connection = AuthServiceProxy("http://%s:%s@%s:%s" %
                                               (username, password, host, port))


    def get_block_hash_at_height(self, block_height):
        """Get the hash of the block at the specified height."""
        return self.rpc_connection.getblockhash(block_height)


    def get_json_for_block_hash(self, block_hash):
        """Get a JSON representation of all transactions at specified height."""
        return self.rpc_connection.getblock(block_hash)


    def _get_raw_tx(self, tx_id):
        """Returns tx in raw format.

        If the requested transaction is the sole transaction of the genesis
        block, bitcoind's RPC interface will throw an error 'No information
        available about transaction (code -5)' so we preempt this by raising an
        error. Iterating callers should just move on to the next tx or block.
        """
        if tx_id == ('4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7af'
                     'deda33b'):
            raise NoDataAvailableForGenesisBlockError
        else:
            return self.rpc_connection.getrawtransaction(tx_id)


    def get_decoded_tx(self, tx_id):
        """Returns a human-readable string of the transaction in JSON format."""
        #print "DEBUG: get_decoded_tx %s" % tx_id
        try:
            return self.rpc_connection.decoderawtransaction(
                self._get_raw_tx(tx_id))
        except NoDataAvailableForGenesisBlockError:
            #bitcoind won't generate this, but here's what it would look like
            genesis_json = {
                'txid':    ('4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2'
                            '127b7afdeda33b'),
                'version':  1,
                'locktime': 0,
                'vin': [{
                    "sequence":4294967295,
                    'coinbase': ('04ffff001d0104455468652054696d65732030332f4a6'
                                 '16e2f32303039204368616e63656c6c6f72206f6e2062'
                                 '72696e6b206f66207365636f6e64206261696c6f75742'
                                 '0666f722062616e6b73')
                }],
                'vout': [
                    {
                        'value': 50.00000000,
                        'n': 0,
                        'scriptPubKey': {
                            'asm': ('04678afdb0fe5548271967f1a67130b7105cd6a828'
                                    'e03909a67962e0ea1f61deb649f6bc3f4cef38c4f3'
                                    '5504e51ec112de5c384df7ba0b8d578a4c702b6bf1'
                                    '1d5f OP_CHECKSIG'),
                            'hex': ('4104678afdb0fe5548271967f1a67130b7105cd6a8'
                                    '28e03909a67962e0ea1f61deb649f6bc3f4cef38c4'
                                    'f35504e51ec112de5c384df7ba0b8d578a4c702b6b'
                                    'f11d5fac'),
                            'reqSigs': 1,
                            'type': 'pubkey',
                            'addresses': ['1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa']
                        }
                    }
                ]
            }
            return genesis_json


    def get_decoded_script(self, asm):
        """Convert bitcoind's 'asm' value to decoded format."""
        return self.rpc_connection.decodescript(asm)


class WalletExplorerReader(object):
    """Fetches cluster data from the WalletExplorer.com API."""

    def __init__(self):
        _, _, _, _, self.api_key = get_config_settings()


    def get_wallet_id(self, tx_id):
        """Get the wallet_id from API for as the sender for specified tx.

        Raises: NoWalletIDForCoinbaseTransaction
        """
        url = get_tx_wallet_info_url(tx_id, self.api_key)
        wallet_json = json.loads(http.fetch_request(url))
        try:
            return wallet_json['wallet_id']
        except KeyError:
            if wallet_json['is_coinbase']:
                raise NoWalletIDForCoinbaseTransaction
            raise KeyError("Could not retrieve wallet_id for %s" % tx_id)
