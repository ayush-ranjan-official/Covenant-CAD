"""
Covenant-CAD Configuration
All settings in one place — no hardcoded values scattered across files.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # Load from .env file

# === STARKNET SEPOLIA (FREE TESTNET) ===
STARKNET_RPC_PRIMARY = os.getenv(
    "STARKNET_RPC_PRIMARY",
    "https://api.cartridge.gg/x/starknet/sepolia"
)
STARKNET_RPC_FALLBACK = os.getenv(
    "STARKNET_RPC_FALLBACK",
    "https://rpc.starknet-testnet.lava.build"
)

# Deployed contract addresses (UPDATE AFTER DEPLOYMENT)
REGISTRY_CONTRACT_ADDRESS = os.getenv("REGISTRY_CONTRACT_ADDRESS", "")
VERIFIER_CONTRACT_ADDRESS = os.getenv("VERIFIER_CONTRACT_ADDRESS", "")

# === BITCOIN SIGNET (FREE TESTNET) ===
WALLET_FILE = os.getenv("WALLET_FILE", "covenant_wallet.json")

# Destination address for covenant payouts (UPDATE WITH YOUR OWN)
# This is where funds go when a covenant is executed
VAULT_DESTINATION_ADDRESS = os.getenv("VAULT_DESTINATION_ADDRESS", "")

# Amount to send when covenant triggers (in satoshis)
COVENANT_PAYOUT_SATS = int(os.getenv("COVENANT_PAYOUT_SATS", "1000"))

# === NODE SETTINGS ===
TARGET_VAULT_ID = int(os.getenv("TARGET_VAULT_ID", "1"))
WS_PORT = int(os.getenv("WS_PORT", "8080"))
UI_PORT = int(os.getenv("UI_PORT", "8000"))
POLL_INTERVAL_SECS = int(os.getenv("POLL_INTERVAL_SECS", "3"))

# === EXPLORER URLS (for UI links) ===
SIGNET_EXPLORER = "https://mempool.space/signet"
STARKNET_EXPLORER = "https://sepolia.voyager.online"

# === DEMO MODE ===
# Set DEMO_FORCE=1 to skip Starknet listening and auto-trigger
DEMO_FORCE = os.getenv("DEMO_FORCE", "0") == "1"
