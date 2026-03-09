"""
Covenant-CAD Node: The Hand
Watches Starknet Sepolia for PullAuthorized events and constructs + broadcasts
real Bitcoin Signet transactions.

All testnets — zero cost:
- Starknet Sepolia: https://starknet-faucet.vercel.app/
- Bitcoin Signet: https://signetfaucet.com/
"""

import asyncio
import json
import os
import sys
from aiohttp import web
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.selector import get_selector_from_name

from config import (
    STARKNET_RPC_PRIMARY, STARKNET_RPC_FALLBACK,
    REGISTRY_CONTRACT_ADDRESS, WALLET_FILE,
    VAULT_DESTINATION_ADDRESS, COVENANT_PAYOUT_SATS,
    TARGET_VAULT_ID, WS_PORT, POLL_INTERVAL_SECS,
    SIGNET_EXPLORER, STARKNET_EXPLORER, DEMO_FORCE
)
from bitcoin_wallet import SignetWallet

# --- VALIDATION ---
if not REGISTRY_CONTRACT_ADDRESS or REGISTRY_CONTRACT_ADDRESS == "0x_YOUR_REGISTRY_ADDRESS":
    print("ERROR: Set REGISTRY_CONTRACT_ADDRESS in .env file")
    print("   Deploy contracts first, then update .env")
    sys.exit(1)

# --- BITCOIN WALLET ---
if os.path.exists(WALLET_FILE):
    wallet = SignetWallet.load_from_file(WALLET_FILE)
    print(f"Loaded existing Signet wallet: {wallet.address_str}")
else:
    wallet = SignetWallet()
    wallet.save_to_file(WALLET_FILE)
    print(f"Created new Signet wallet: {wallet.address_str}")
    print(f"   Fund it at https://signetfaucet.com/ or https://signet.bc-2.jp")
    print(f"   Send sBTC to: {wallet.address_str}")

# --- EVENT SETUP ---
EVENT_NAME = "PullAuthorized"
EVENT_SELECTOR = get_selector_from_name(EVENT_NAME)
print(f"Event Selector for '{EVENT_NAME}': {hex(EVENT_SELECTOR)}")

# Convert contract address to int for starknet-py
CONTRACT_INT = int(REGISTRY_CONTRACT_ADDRESS, 16)

# --- STATE ---
connected_clients = set()
processed_tx_hashes = set()
last_block_num = 0

# --- PERSISTENCE (Atomic writes) ---
PERSISTENCE_FILE = "node_state.json"

def save_persistence():
    data = {
        "processed_txs": list(processed_tx_hashes),
        "last_block": last_block_num
    }
    with open(PERSISTENCE_FILE + ".tmp", "w") as f:
        json.dump(data, f)
    os.replace(PERSISTENCE_FILE + ".tmp", PERSISTENCE_FILE)

def load_persistence():
    global processed_tx_hashes, last_block_num
    if os.path.exists(PERSISTENCE_FILE):
        try:
            with open(PERSISTENCE_FILE, "r") as f:
                data = json.load(f)
                processed_tx_hashes = set(data.get("processed_txs", []))
                last_block_num = data.get("last_block", 0)
                print(f"Loaded state: block {last_block_num}, {len(processed_tx_hashes)} processed txs")
        except Exception as e:
            print(f"Warning: Failed to load persistence: {e}")

# --- HTTP/WS HANDLERS ---
async def health_check(request):
    balance = 0
    try:
        balance = wallet.get_balance()
    except:
        pass

    return web.json_response({
        "status": "healthy",
        "mode": "OFFLINE_DEMO" if DEMO_FORCE else "LIVE_SIGNET",
        "last_block": last_block_num,
        "processed_count": len(processed_tx_hashes),
        "bitcoin_wallet": wallet.address_str,
        "bitcoin_balance_sats": balance,
        "starknet_contract": REGISTRY_CONTRACT_ADDRESS,
        "network": {
            "starknet": "Sepolia (testnet)",
            "bitcoin": "Signet (testnet)"
        }
    })

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    connected_clients.add(ws)

    if DEMO_FORCE:
        mode_msg = "OFFLINE DEMO MODE"
    else:
        mode_msg = "LIVE — Starknet Sepolia + Bitcoin Signet"

    balance = 0
    try:
        balance = wallet.get_balance()
    except:
        pass

    await ws.send_json({
        "type": "status",
        "msg": mode_msg,
        "vault_state": "LOCKED",
        "wallet_address": wallet.address_str,
        "wallet_balance_sats": balance,
        "starknet_contract": REGISTRY_CONTRACT_ADDRESS,
        "explorer_starknet": f"{STARKNET_EXPLORER}/contract/{REGISTRY_CONTRACT_ADDRESS}",
        "explorer_bitcoin": f"{SIGNET_EXPLORER}/address/{wallet.address_str}"
    })

    try:
        async for msg in ws:
            pass
    finally:
        connected_clients.discard(ws)
    return ws

async def notify_frontend(data):
    for ws in list(connected_clients):
        try:
            await ws.send_json(data)
        except:
            connected_clients.discard(ws)

# --- CORE: REAL BITCOIN TRANSACTION ---
async def execute_bitcoin_logic(vault_id, starknet_tx_hash=None):
    """
    Constructs and broadcasts a REAL Bitcoin Signet transaction.
    This is NOT a simulation — the transaction appears on mempool.space/signet.
    """
    print(f"\n{'='*60}")
    print(f"EXECUTING COVENANT FOR VAULT {vault_id}")
    print(f"{'='*60}")

    if starknet_tx_hash:
        starknet_url = f"{STARKNET_EXPLORER}/tx/{starknet_tx_hash}"
        print(f"Starknet TX: {starknet_url}")

    await notify_frontend({
        "type": "unlocking",
        "vault_id": vault_id,
        "starknet_tx": starknet_tx_hash,
        "starknet_url": f"{STARKNET_EXPLORER}/tx/{starknet_tx_hash}" if starknet_tx_hash else None
    })

    # Check wallet balance
    try:
        balance = wallet.get_balance()
        print(f"Wallet balance: {balance} sats")

        if balance < COVENANT_PAYOUT_SATS + 300:  # amount + fee
            error_msg = (
                f"Insufficient funds ({balance} sats). "
                f"Need at least {COVENANT_PAYOUT_SATS + 300} sats. "
                f"Fund wallet at https://signetfaucet.com/ -> {wallet.address_str}"
            )
            print(f"ERROR: {error_msg}")
            await notify_frontend({
                "type": "error",
                "vault_id": vault_id,
                "error": error_msg,
                "fund_url": "https://signetfaucet.com/",
                "wallet_address": wallet.address_str
            })
            return

        # Determine destination
        dest = VAULT_DESTINATION_ADDRESS
        if not dest or dest == "tb1q_YOUR_DESTINATION_ADDRESS":
            # If no destination set, send to self (demonstrates the tx construction)
            dest = wallet.address_str
            print(f"No destination set, sending to self for demonstration")

        # BUILD REAL TRANSACTION
        print(f"Constructing Bitcoin Signet transaction...")
        print(f"   From:   {wallet.address_str}")
        print(f"   To:     {dest}")
        print(f"   Amount: {COVENANT_PAYOUT_SATS} sats")

        raw_tx = wallet.create_transaction(
            to_address=dest,
            amount_sats=COVENANT_PAYOUT_SATS,
            fee_sats=300
        )
        print(f"Raw TX constructed ({len(raw_tx)//2} bytes)")

        # BROADCAST REAL TRANSACTION
        print(f"Broadcasting to Bitcoin Signet...")
        txid = wallet.broadcast_transaction(raw_tx)

        explorer_url = f"{SIGNET_EXPLORER}/tx/{txid}"
        print(f"\nCOVENANT EXECUTED SUCCESSFULLY!")
        print(f"   Bitcoin TX: {txid}")
        print(f"   Explorer:   {explorer_url}")
        print(f"{'='*60}\n")

        await notify_frontend({
            "type": "success",
            "vault_id": vault_id,
            "tx_hash": txid,
            "explorer_url": explorer_url,
            "starknet_tx": starknet_tx_hash,
            "amount_sats": COVENANT_PAYOUT_SATS,
            "destination": dest
        })

    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: Bitcoin TX failed: {error_msg}")
        await notify_frontend({
            "type": "error",
            "vault_id": vault_id,
            "error": error_msg
        })

# --- STARKNET EVENT LISTENER ---
async def starknet_listener():
    global last_block_num

    if DEMO_FORCE:
        print("\nDEMO_FORCE MODE — Skipping Starknet listener")
        print("   Will auto-trigger covenant execution in 5 seconds...")
        await asyncio.sleep(5)
        await execute_bitcoin_logic(TARGET_VAULT_ID, starknet_tx_hash="DEMO_MODE")
        return

    current_rpc = STARKNET_RPC_PRIMARY
    client = FullNodeClient(node_url=current_rpc)
    load_persistence()

    # Dynamic start block
    if last_block_num == 0:
        try:
            latest = await client.get_block("latest")
            last_block_num = max(0, latest.block_number - 5)
            print(f"First run. Starting from block {last_block_num}")
        except Exception as e:
            print(f"Warning: Startup failed: {e}. Will retry...")

    print(f"\nWatching Starknet Contract: {REGISTRY_CONTRACT_ADDRESS}")
    print(f"   RPC: {current_rpc}")
    print(f"   Target Vault ID: {TARGET_VAULT_ID}")
    print(f"   Polling every {POLL_INTERVAL_SECS}s\n")

    while True:
        try:
            latest = await client.get_block("latest")
            if latest.block_number <= last_block_num:
                await asyncio.sleep(POLL_INTERVAL_SECS)
                continue

            events_resp = await client.get_events(
                address=CONTRACT_INT,
                keys=[[EVENT_SELECTOR]],
                from_block_number=last_block_num + 1,
                to_block_number=latest.block_number,
                follow_continuation_token=True
            )

            for event in events_resp.events:
                tx_hash_hex = hex(event.transaction_hash)
                if tx_hash_hex in processed_tx_hashes:
                    continue

                processed_tx_hashes.add(tx_hash_hex)
                save_persistence()

                vault_id = int(event.data[0])
                print(f"\nPullAuthorized event detected!")
                print(f"   Vault ID: {vault_id}")
                print(f"   Starknet TX: {tx_hash_hex}")

                if vault_id == TARGET_VAULT_ID:
                    await execute_bitcoin_logic(vault_id, starknet_tx_hash=tx_hash_hex)
                else:
                    print(f"   Vault {vault_id} != target {TARGET_VAULT_ID}, skipping")

            last_block_num = latest.block_number
            save_persistence()
            await asyncio.sleep(POLL_INTERVAL_SECS)

        except Exception as e:
            print(f"Warning: RPC Error: {e}")
            if current_rpc == STARKNET_RPC_PRIMARY:
                current_rpc = STARKNET_RPC_FALLBACK
                print(f"Switching to fallback: {current_rpc}")
            else:
                current_rpc = STARKNET_RPC_PRIMARY
                print(f"Switching to primary: {current_rpc}")
            client = FullNodeClient(node_url=current_rpc)
            await asyncio.sleep(5)

# --- MAIN ---
async def main():
    # Print startup banner
    print(f"\n{'='*60}")
    print(f"  COVENANT-CAD NODE")
    print(f"  Bitcoin OP_CAT Covenant Simulator")
    print(f"{'='*60}")
    print(f"  Starknet: Sepolia (testnet) — FREE")
    print(f"  Bitcoin:  Signet (testnet) — FREE")
    print(f"  Contract: {REGISTRY_CONTRACT_ADDRESS}")
    print(f"  Wallet:   {wallet.address_str}")
    try:
        bal = wallet.get_balance()
        print(f"  Balance:  {bal} sats")
    except:
        print(f"  Balance:  (unable to fetch)")
    print(f"{'='*60}\n")

    app = web.Application()
    app.add_routes([
        web.get('/ws', websocket_handler),
        web.get('/health', health_check)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', WS_PORT)
    await site.start()
    print(f"WebSocket server on port {WS_PORT}")
    print(f"Health check: http://localhost:{WS_PORT}/health\n")

    await starknet_listener()

if __name__ == "__main__":
    asyncio.run(main())
