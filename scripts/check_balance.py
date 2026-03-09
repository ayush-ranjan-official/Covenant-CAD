"""Check Signet wallet balance."""
import sys
sys.path.insert(0, '../node')
from bitcoin_wallet import SignetWallet

wallet = SignetWallet.load_from_file("../node/covenant_wallet.json")
wallet.info()
