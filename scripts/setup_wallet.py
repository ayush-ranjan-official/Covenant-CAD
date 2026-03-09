"""
Step 1: Generate a Bitcoin Signet wallet for the Covenant Node.
Run this FIRST before anything else.
"""
import sys
sys.path.insert(0, '../node')
from bitcoin_wallet import SignetWallet

print("Covenant-CAD Wallet Setup")
print("=" * 50)

wallet = SignetWallet()
wallet.save_to_file("../node/covenant_wallet.json")

print(f"\nWallet created!")
print(f"\nNEXT STEPS:")
print(f"   1. Go to https://signetfaucet.com/")
print(f"   2. Enter address: {wallet.address_str}")
print(f"   3. Request 0.01 sBTC (free!)")
print(f"   4. Wait ~1-2 minutes for confirmation")
print(f"   5. Run: python check_balance.py")
