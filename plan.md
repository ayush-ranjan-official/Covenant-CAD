# Covenant-CAD: COMPLETE Build Plan for Claude Code
# ====================================================
# ZERO COST — Everything runs on free testnets
# ZERO HARDCODING — Every component is real and end-to-end functional
# ====================================================

## ⚠️ SKILL FILES TO READ BEFORE STARTING

**BEFORE writing any code, read these skill files for best practices:**
- For the UI : use `/frontend-design` plugin — this contains
  critical guidelines for creating visually distinctive, non-generic frontends. The UI section below
  has extremely detailed design specs. Follow them precisely — do NOT fall back to generic dark-mode
  templates, purple gradients, Inter/Roboto fonts, or rounded-card layouts.

## CRITICAL CONSTRAINTS
- **NO mainnet tokens or real money required anywhere**
- **Starknet Sepolia** = free testnet (faucet: https://starknet-faucet.vercel.app/)
- **Bitcoin Signet** = free testnet (faucet: https://signetfaucet.com/ or https://signet.bc-2.jp)
- **No hardcoded transaction hashes** — real Bitcoin Signet transactions are constructed, signed, and broadcast
- **No mocked verifier** — deploy a real verifier contract that the registry actually calls
- **No mocked event listening** — real Starknet event polling

---

## PROJECT OVERVIEW

**One-liner:** A developer sandbox that simulates Bitcoin OP_CAT covenants today, using Starknet as the enforcement layer ("The Brain") and a Python node as the executor ("The Hand").

**Flow (fully real):**
1. User registers a covenant vault on Starknet Sepolia (free)
2. User calls `execute_pull` with proof data → Starknet contract calls verifier, emits `PullAuthorized` event
3. Python node detects the real event on Starknet Sepolia
4. Node constructs a real Bitcoin Signet transaction, signs it with a real private key
5. Node broadcasts the transaction to Bitcoin Signet via Blockstream Esplora API (free, no auth)
6. UI displays the real Signet transaction hash — verifiable on https://mempool.space/signet/

---

## ARCHITECTURE

```
┌──────────────────────────┐     ┌────────────────────────────┐     ┌──────────────────────┐
│   THE BRAIN              │     │   THE HAND                 │     │   THE VAULT           │
│   (Starknet Sepolia)     │────▶│   (Covenant Node - Python) │────▶│   (Bitcoin Signet)    │
│                          │     │                            │     │                       │
│ - CovenantRegistry.cairo │     │ - Watches PullAuthorized   │     │ - Real sBTC wallet    │
│ - SimpleVerifier.cairo   │     │   events via starknet-py   │     │ - Real UTXO spending  │
│ - Real ZK stub verifier  │     │ - Constructs real Bitcoin  │     │ - Viewable on         │
│ - PullAuthorized event   │     │   Signet transactions      │     │   mempool.space/signet│
│                          │     │ - Broadcasts via Esplora   │     │                       │
│ FREE: Sepolia faucet     │     │   API (no auth needed)     │     │ FREE: Signet faucet   │
└──────────────────────────┘     └────────────────────────────┘     └──────────────────────┘
                                          │
                                          ▼
                                ┌────────────────────────────┐
                                │   VISUALIZER (UI)          │
                                │   - WebSocket live updates │
                                │   - Real tx hash + explorer│
                                │     link to mempool.space  │
                                └────────────────────────────┘
```

### Trust Model (Include in README and slides verbatim)
```
🛡️ TRUST MODEL & ARCHITECTURE (RESEARCH PROTOTYPE)

Context: This project simulates Bitcoin OP_CAT capabilities to demonstrate
Starknet as an execution layer for Bitcoin covenant logic.

1. The Brain (Starknet Sepolia): Validates covenant conditions, calls an
   on-chain verifier contract (Garaga-interface-compatible stub), and emits
   the PullAuthorized event upon successful verification.

2. The Hand (Covenant Node): An off-chain Python signer that watches Starknet
   events and constructs + broadcasts real Bitcoin Signet transactions. Acts
   as a Temporary Relayer.

3. The Vault (Bitcoin Signet): Holds real (testnet) sBTC. Transactions are
   publicly verifiable on mempool.space/signet.

Note: In this prototype, the Python Node acts as a trusted relayer simulating
the future where Bitcoin can verify STARK proofs directly (post-OP_CAT).
The verifier contract is a simplified stub implementing the Garaga verifier
interface — in production, this would be a full Groth16/STARK verifier.
```

---

## DIRECTORY STRUCTURE

```
covenant-cad/
├── README.md
├── contracts/
│   ├── Scarb.toml
│   └── src/
│       ├── lib.cairo
│       ├── covenant_registry.cairo    # Main registry contract
│       └── simple_verifier.cairo      # Verifier contract (Garaga interface stub)
├── node/
│   ├── covenant_node.py               # Main event listener + Bitcoin tx builder
│   ├── bitcoin_wallet.py              # Real Bitcoin Signet wallet management
│   ├── config.py                      # All configuration in one place
│   ├── requirements.txt
│   └── .env.example                   # Environment variable template
├── ui/
│   └── index.html                     # Single-file visualizer
├── scripts/
│   ├── setup_wallet.py                # Generate Bitcoin Signet wallet + show faucet instructions
│   ├── register_vault.py              # Register a covenant on Starknet
│   ├── trigger_pull.py                # Trigger execute_pull on Starknet
│   └── check_balance.py              # Check Signet wallet balance
└── docs/
    └── architecture.md
```

---

## COMPONENT 1: STARKNET CONTRACTS (Cairo)

### Important: Two contracts are deployed — the Registry AND the Verifier

### File: `contracts/Scarb.toml`

```toml
[package]
name = "covenant_cad"
version = "0.1.0"
edition = "2024_07"

[dependencies]
starknet = ">=2.9.1"

[[target.starknet-contract]]
sierra = true
casm = true
```

### File: `contracts/src/lib.cairo`

```cairo
mod covenant_registry;
mod simple_verifier;
```

### File: `contracts/src/simple_verifier.cairo`

**This is NOT a mock — it's a real deployed contract that the registry calls.**
It implements the same interface Garaga uses, so swapping in real Garaga later is a 1-line change.

```cairo
/// A simplified verifier contract implementing the Garaga verifier interface.
/// This contract performs basic validation (non-empty proof, correct public input count)
/// rather than just returning true blindly.
///
/// In production, replace this contract address with a real Garaga Groth16 verifier.
/// Garaga docs: https://garaga.gitbook.io/garaga
/// Scaffold-Garaga: https://github.com/KevinSheeranxyj/scaffold-garaga

#[starknet::interface]
trait ISimpleVerifier<TContractState> {
    fn verify_groth16(
        ref self: TContractState,
        proof: Array<felt252>,
        public_inputs: Array<felt252>
    ) -> bool;
}

#[starknet::contract]
mod SimpleVerifier {
    #[storage]
    struct Storage {
        verification_count: u64,
    }

    #[event]
    #[derive(Drop, starknet::Event)]
    enum Event {
        ProofVerified: ProofVerified,
    }

    #[derive(Drop, starknet::Event)]
    struct ProofVerified {
        proof_length: u32,
        public_inputs_length: u32,
        timestamp: u64,
    }

    #[abi(embed_v0)]
    impl SimpleVerifierImpl of super::ISimpleVerifier<ContractState> {
        fn verify_groth16(
            ref self: ContractState,
            proof: Array<felt252>,
            public_inputs: Array<felt252>
        ) -> bool {
            // Real validation: proof must be non-empty
            let proof_len = proof.len();
            assert(proof_len > 0, 'EMPTY_PROOF');

            // Real validation: must have at least 1 public input
            let pi_len = public_inputs.len();
            assert(pi_len > 0, 'EMPTY_PUBLIC_INPUTS');

            // Increment verification counter (on-chain state change = real)
            let current = self.verification_count.read();
            self.verification_count.write(current + 1);

            // Emit real event for audit trail
            self.emit(Event::ProofVerified(ProofVerified {
                proof_length: proof_len,
                public_inputs_length: pi_len,
                timestamp: starknet::info::get_block_timestamp(),
            }));

            // In production: full Groth16 verification via Garaga
            // For sandbox: accept valid-structured proofs
            true
        }
    }
}
```

### File: `contracts/src/covenant_registry.cairo`

**Key change: This contract ACTUALLY CALLS the verifier contract — not commented out.**

```cairo
#[starknet::interface]
trait ICovenantRegistry<TContractState> {
    fn register_covenant(ref self: TContractState, vault_id: felt252, conditions_hash: felt252);
    fn execute_pull(
        ref self: TContractState,
        vault_id: felt252,
        proof: Array<felt252>,
        public_inputs: Array<felt252>
    );
    fn get_covenant(self: @TContractState, vault_id: felt252) -> felt252;
    fn is_vault_spent(self: @TContractState, vault_id: felt252) -> bool;
    fn get_verifier_address(self: @TContractState) -> starknet::ContractAddress;
}

// Interface matching our SimpleVerifier (and Garaga's interface)
#[starknet::interface]
trait IVerifier<TContractState> {
    fn verify_groth16(
        ref self: TContractState,
        proof: Array<felt252>,
        public_inputs: Array<felt252>
    ) -> bool;
}

#[starknet::contract]
mod CovenantRegistry {
    use starknet::get_caller_address;
    use starknet::ContractAddress;
    use starknet::storage::Map;  // Modern Map (replaces LegacyMap since Cairo 2.7+)
    use super::{IVerifierDispatcher, IVerifierDispatcherTrait};

    #[storage]
    struct Storage {
        covenants: Map<felt252, felt252>,       // vault_id -> conditions_hash
        authorized_pulls: Map<felt252, bool>,   // vault_id -> spent (replay protection)
        verifier_address: ContractAddress,       // Address of deployed verifier contract
        owner: ContractAddress,                  // Contract deployer
    }

    #[constructor]
    fn constructor(ref self: ContractState, verifier_address: ContractAddress) {
        self.verifier_address.write(verifier_address);
        self.owner.write(get_caller_address());
    }

    #[event]
    #[derive(Drop, starknet::Event)]
    enum Event {
        CovenantRegistered: CovenantRegistered,
        PullAuthorized: PullAuthorized,
    }

    #[derive(Drop, starknet::Event)]
    struct CovenantRegistered {
        vault_id: felt252,
        conditions_hash: felt252,
        registrar: ContractAddress,
    }

    #[derive(Drop, starknet::Event)]
    struct PullAuthorized {
        vault_id: felt252,
        timestamp: u64,
    }

    #[abi(embed_v0)]
    impl CovenantRegistryImpl of super::ICovenantRegistry<ContractState> {

        fn register_covenant(ref self: ContractState, vault_id: felt252, conditions_hash: felt252) {
            // Prevent re-registration of existing vaults
            let existing = self.covenants.entry(vault_id).read();
            assert(existing == 0, 'VAULT_ALREADY_EXISTS');

            // Conditions hash must be non-zero
            assert(conditions_hash != 0, 'INVALID_CONDITIONS');

            self.covenants.entry(vault_id).write(conditions_hash);

            self.emit(Event::CovenantRegistered(CovenantRegistered {
                vault_id: vault_id,
                conditions_hash: conditions_hash,
                registrar: get_caller_address(),
            }));
        }

        fn get_covenant(self: @ContractState, vault_id: felt252) -> felt252 {
            self.covenants.entry(vault_id).read()
        }

        fn is_vault_spent(self: @ContractState, vault_id: felt252) -> bool {
            self.authorized_pulls.entry(vault_id).read()
        }

        fn get_verifier_address(self: @ContractState) -> ContractAddress {
            self.verifier_address.read()
        }

        fn execute_pull(
            ref self: ContractState,
            vault_id: felt252,
            proof: Array<felt252>,
            public_inputs: Array<felt252>
        ) {
            // --- SECURITY CHECK 1: Vault must exist ---
            let conditions = self.covenants.entry(vault_id).read();
            assert(conditions != 0, 'UNKNOWN_VAULT');

            // --- SECURITY CHECK 2: Replay protection (one-shot) ---
            let already_done = self.authorized_pulls.entry(vault_id).read();
            assert(!already_done, 'VAULT_ALREADY_SPENT');

            // --- REAL VERIFIER CALL (not a comment/stub!) ---
            // This actually calls the deployed SimpleVerifier contract
            // In production: point verifier_address to Garaga's Groth16 verifier
            let verifier = IVerifierDispatcher {
                contract_address: self.verifier_address.read()
            };
            let is_valid = verifier.verify_groth16(proof, public_inputs);
            assert(is_valid, 'PROOF_VERIFICATION_FAILED');

            // --- Mark as spent (replay protection) ---
            self.authorized_pulls.entry(vault_id).write(true);

            // --- Emit event (this is what the Python node watches for) ---
            self.emit(Event::PullAuthorized(PullAuthorized {
                vault_id: vault_id,
                timestamp: starknet::info::get_block_timestamp(),
            }));
        }
    }
}
```

### Build & Deploy Steps (All Free on Sepolia)

```bash
# === PREREQUISITES ===
# Install Scarb: https://docs.starknet.io/quick-start/environment-setup/
# Install Starknet Foundry: https://foundry-rs.github.io/starknet-foundry/getting-started/installation

# === WALLET SETUP (FREE) ===
# Option A: Use sncast to create an account
sncast account create --name covenant_dev --network sepolia
# Fund it: Go to https://starknet-faucet.vercel.app/ and paste your address
# Wait for faucet tx to confirm, then deploy:
sncast account deploy --name covenant_dev --network sepolia

# Option B: Use Argent X or Braavos browser wallet
# - Install extension, create wallet, switch to Sepolia
# - Get free STRK from https://starknet-faucet.vercel.app/
# - Export private key for sncast usage

# === BUILD ===
cd contracts
scarb build
# Output: target/dev/covenant_cad_CovenantRegistry.contract_class.json
# Output: target/dev/covenant_cad_SimpleVerifier.contract_class.json

# === DEPLOY STEP 1: Deploy the Verifier first ===
sncast --account covenant_dev declare \
    --contract-name SimpleVerifier \
    --network sepolia
# Save the CLASS_HASH_VERIFIER from output

sncast --account covenant_dev deploy \
    --class-hash <CLASS_HASH_VERIFIER> \
    --network sepolia
# Save the VERIFIER_ADDRESS from output

# === DEPLOY STEP 2: Deploy the Registry with verifier address ===
sncast --account covenant_dev declare \
    --contract-name CovenantRegistry \
    --network sepolia
# Save the CLASS_HASH_REGISTRY from output

sncast --account covenant_dev deploy \
    --class-hash <CLASS_HASH_REGISTRY> \
    --constructor-calldata <VERIFIER_ADDRESS> \
    --network sepolia
# Save the REGISTRY_ADDRESS from output

# === VERIFY DEPLOYMENT ===
# Check verifier address stored in registry:
sncast --account covenant_dev call \
    --contract-address <REGISTRY_ADDRESS> \
    --function get_verifier_address \
    --network sepolia
# Should return VERIFIER_ADDRESS
```

---

## COMPONENT 2: BITCOIN SIGNET WALLET (Python)

### File: `node/bitcoin_wallet.py`

**This is a REAL Bitcoin Signet wallet — creates real transactions, broadcasts to real Signet network.**

```python
"""
Bitcoin Signet Wallet for Covenant-CAD
Uses python-bitcoinlib for transaction construction.
Broadcasts via Blockstream Esplora API (free, no auth).

Bitcoin Signet is a free testnet:
- Faucet: https://signetfaucet.com/ or https://signet.bc-2.jp
- Explorer: https://mempool.space/signet/
- Esplora API: https://blockstream.info/signet/api/
"""

import hashlib
import os
import json
import requests

# python-bitcoinlib with Signet support
import bitcoin
from bitcoin.core import (
    CMutableTransaction, CMutableTxIn, CMutableTxOut,
    COutPoint, lx, b2x, b2lx, CScript
)
from bitcoin.core.script import (
    CScript, OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG,
    SignatureHash, SIGHASH_ALL
)
from bitcoin.wallet import CBitcoinSecret, P2WPKHBitcoinAddress, CBitcoinAddress
from bitcoin.core.scripteval import VerifyScript

# Select Signet network
bitcoin.SelectParams('signet')

# Blockstream Esplora API for Signet (free, no authentication needed)
ESPLORA_BASE = "https://blockstream.info/signet/api"

# Mempool.space Signet API as fallback
MEMPOOL_BASE = "https://mempool.space/signet/api"


class SignetWallet:
    """Real Bitcoin Signet wallet with transaction construction and broadcast."""

    def __init__(self, private_key_wif: str = None):
        """
        Initialize wallet.
        Args:
            private_key_wif: WIF-encoded private key. If None, generates new one.
        """
        if private_key_wif:
            self.secret = CBitcoinSecret(private_key_wif)
        else:
            # Generate new random private key
            secret_bytes = os.urandom(32)
            self.secret = CBitcoinSecret.from_secret_bytes(secret_bytes, compressed=True)

        self.public_key = self.secret.pub
        self.address = P2WPKHBitcoinAddress.from_pubkey(self.public_key)

    @property
    def address_str(self) -> str:
        return str(self.address)

    @property
    def wif(self) -> str:
        return str(self.secret)

    def get_utxos(self) -> list:
        """Fetch real UTXOs from Esplora API."""
        url = f"{ESPLORA_BASE}/address/{self.address_str}/utxo"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"⚠️ Esplora UTXO fetch failed: {e}, trying mempool.space...")
            # Fallback to mempool.space
            url = f"{MEMPOOL_BASE}/address/{self.address_str}/utxo"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()

    def get_balance(self) -> int:
        """Get total balance in satoshis."""
        utxos = self.get_utxos()
        return sum(u['value'] for u in utxos)

    def create_transaction(self, to_address: str, amount_sats: int, fee_sats: int = 300) -> str:
        """
        Create, sign, and return a raw Bitcoin Signet transaction (hex).
        This is a REAL transaction that can be broadcast to Signet.

        Args:
            to_address: Destination Bitcoin Signet address
            amount_sats: Amount to send in satoshis
            fee_sats: Transaction fee in satoshis (Signet fees are minimal)

        Returns:
            Raw transaction hex string
        """
        utxos = self.get_utxos()
        if not utxos:
            raise Exception(f"No UTXOs available. Fund wallet at https://signetfaucet.com/ with address: {self.address_str}")

        # Select UTXOs (simple: use first sufficient UTXO)
        selected_utxos = []
        total_input = 0
        needed = amount_sats + fee_sats

        for utxo in utxos:
            selected_utxos.append(utxo)
            total_input += utxo['value']
            if total_input >= needed:
                break

        if total_input < needed:
            raise Exception(
                f"Insufficient funds. Have {total_input} sats, need {needed} sats. "
                f"Fund wallet at https://signetfaucet.com/ with address: {self.address_str}"
            )

        # Build transaction inputs
        txins = []
        for utxo in selected_utxos:
            outpoint = COutPoint(lx(utxo['txid']), utxo['vout'])
            txins.append(CMutableTxIn(outpoint))

        # Build transaction outputs
        txouts = []

        # Output 1: Payment to destination
        dest_address = CBitcoinAddress(to_address)
        txouts.append(CMutableTxOut(amount_sats, dest_address.to_scriptPubKey()))

        # Output 2: Change back to self (if any)
        change = total_input - amount_sats - fee_sats
        if change > 546:  # Dust threshold
            txouts.append(CMutableTxOut(change, self.address.to_scriptPubKey()))

        # Create transaction
        tx = CMutableTransaction(txins, txouts)

        # Sign each input
        for i, utxo in enumerate(selected_utxos):
            # For P2WPKH (SegWit), use witness signing
            script_code = CScript([
                OP_DUP, OP_HASH160,
                bitcoin.core.Hash160(self.public_key),
                OP_EQUALVERIFY, OP_CHECKSIG
            ])
            sighash = SignatureHash(
                script_code, tx, i, SIGHASH_ALL,
                amount=utxo['value'],
                sigversion=1  # SIGVERSION_WITNESS_V0
            )
            sig = self.secret.sign(sighash) + bytes([SIGHASH_ALL])

            # Set witness data
            tx.wit.vtxinwit[i].scriptWitness.stack = [sig, self.public_key]

        return b2x(tx.serialize())

    def broadcast_transaction(self, raw_tx_hex: str) -> str:
        """
        Broadcast a raw transaction to Bitcoin Signet via Esplora API.
        Returns the transaction ID on success.

        Esplora API docs: https://github.com/Blockstream/esplora/blob/master/API.md
        """
        url = f"{ESPLORA_BASE}/tx"
        try:
            resp = requests.post(url, data=raw_tx_hex, timeout=15)
            if resp.status_code == 200:
                txid = resp.text.strip()
                print(f"✅ Transaction broadcast to Signet! TXID: {txid}")
                print(f"🔍 View on explorer: https://mempool.space/signet/tx/{txid}")
                return txid
            else:
                error_msg = resp.text
                print(f"❌ Broadcast failed: {error_msg}")
                # Fallback to mempool.space
                return self._broadcast_fallback(raw_tx_hex)
        except Exception as e:
            print(f"⚠️ Esplora broadcast failed: {e}, trying fallback...")
            return self._broadcast_fallback(raw_tx_hex)

    def _broadcast_fallback(self, raw_tx_hex: str) -> str:
        """Fallback broadcast via mempool.space Signet API."""
        url = f"{MEMPOOL_BASE}/tx"
        resp = requests.post(url, data=raw_tx_hex, timeout=15)
        if resp.status_code == 200:
            txid = resp.text.strip()
            print(f"✅ [Fallback] Transaction broadcast! TXID: {txid}")
            print(f"🔍 View on explorer: https://mempool.space/signet/tx/{txid}")
            return txid
        else:
            raise Exception(f"All broadcast attempts failed: {resp.text}")

    def save_to_file(self, filepath: str):
        """Save wallet credentials to file (for persistence between runs)."""
        data = {
            "private_key_wif": self.wif,
            "address": self.address_str,
            "network": "signet"
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"💾 Wallet saved to {filepath}")
        print(f"⚠️  Keep this file secret — it contains your private key!")

    @classmethod
    def load_from_file(cls, filepath: str) -> 'SignetWallet':
        """Load wallet from saved file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(private_key_wif=data['private_key_wif'])

    def info(self):
        """Print wallet info."""
        balance = self.get_balance()
        print(f"═══════════════════════════════════════")
        print(f"  Covenant-CAD Bitcoin Signet Wallet")
        print(f"═══════════════════════════════════════")
        print(f"  Network:  Signet (testnet)")
        print(f"  Address:  {self.address_str}")
        print(f"  Balance:  {balance} sats ({balance/1e8:.8f} sBTC)")
        print(f"  UTXOs:    {len(self.get_utxos())}")
        print(f"═══════════════════════════════════════")
        if balance == 0:
            print(f"\n  ⚠️  Wallet is empty!")
            print(f"  Get free Signet coins from:")
            print(f"  → https://signetfaucet.com/")
            print(f"  → https://signet.bc-2.jp/")
            print(f"  Send to: {self.address_str}")
```

---

## COMPONENT 3: CONFIGURATION

### File: `node/config.py`

```python
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
    "https://starknet-sepolia.public.blastapi.io"
)
STARKNET_RPC_FALLBACK = os.getenv(
    "STARKNET_RPC_FALLBACK",
    "https://free-rpc.nethermind.io/sepolia-juno"
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
STARKNET_EXPLORER = "https://sepolia.starkscan.co"

# === DEMO MODE ===
# Set DEMO_FORCE=1 to skip Starknet listening and auto-trigger
DEMO_FORCE = os.getenv("DEMO_FORCE", "0") == "1"
```

### File: `node/.env.example`

```bash
# Starknet Sepolia (free testnet)
STARKNET_RPC_PRIMARY=https://starknet-sepolia.public.blastapi.io
STARKNET_RPC_FALLBACK=https://free-rpc.nethermind.io/sepolia-juno

# Contract addresses (UPDATE AFTER DEPLOYMENT)
REGISTRY_CONTRACT_ADDRESS=0x_YOUR_REGISTRY_ADDRESS
VERIFIER_CONTRACT_ADDRESS=0x_YOUR_VERIFIER_ADDRESS

# Bitcoin Signet (free testnet)
WALLET_FILE=covenant_wallet.json
VAULT_DESTINATION_ADDRESS=tb1q_YOUR_DESTINATION_ADDRESS
COVENANT_PAYOUT_SATS=1000

# Node settings
TARGET_VAULT_ID=1
WS_PORT=8080
DEMO_FORCE=0
```

---

## COMPONENT 4: THE COVENANT NODE (Python)

### File: `node/covenant_node.py`

**Fully real — real events, real Bitcoin transactions, real broadcasts.**

```python
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
    print("❌ ERROR: Set REGISTRY_CONTRACT_ADDRESS in .env file")
    print("   Deploy contracts first, then update .env")
    sys.exit(1)

# --- BITCOIN WALLET ---
if os.path.exists(WALLET_FILE):
    wallet = SignetWallet.load_from_file(WALLET_FILE)
    print(f"💰 Loaded existing Signet wallet: {wallet.address_str}")
else:
    wallet = SignetWallet()
    wallet.save_to_file(WALLET_FILE)
    print(f"🆕 Created new Signet wallet: {wallet.address_str}")
    print(f"   Fund it at https://signetfaucet.com/ or https://signet.bc-2.jp")
    print(f"   Send sBTC to: {wallet.address_str}")

# --- EVENT SETUP ---
EVENT_NAME = "PullAuthorized"
EVENT_SELECTOR = get_selector_from_name(EVENT_NAME)
print(f"🔒 Event Selector for '{EVENT_NAME}': {hex(EVENT_SELECTOR)}")

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
                print(f"📂 Loaded state: block {last_block_num}, {len(processed_tx_hashes)} processed txs")
        except Exception as e:
            print(f"⚠️ Failed to load persistence: {e}")

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
        mode_msg = "⚠️ OFFLINE DEMO MODE"
    else:
        mode_msg = "🟢 LIVE — Starknet Sepolia + Bitcoin Signet"

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
    print(f"⚙️  EXECUTING COVENANT FOR VAULT {vault_id}")
    print(f"{'='*60}")

    if starknet_tx_hash:
        starknet_url = f"{STARKNET_EXPLORER}/tx/{starknet_tx_hash}"
        print(f"📋 Starknet TX: {starknet_url}")

    await notify_frontend({
        "type": "unlocking",
        "vault_id": vault_id,
        "starknet_tx": starknet_tx_hash,
        "starknet_url": f"{STARKNET_EXPLORER}/tx/{starknet_tx_hash}" if starknet_tx_hash else None
    })

    # Check wallet balance
    try:
        balance = wallet.get_balance()
        print(f"💰 Wallet balance: {balance} sats")

        if balance < COVENANT_PAYOUT_SATS + 300:  # amount + fee
            error_msg = (
                f"Insufficient funds ({balance} sats). "
                f"Need at least {COVENANT_PAYOUT_SATS + 300} sats. "
                f"Fund wallet at https://signetfaucet.com/ → {wallet.address_str}"
            )
            print(f"❌ {error_msg}")
            await notify_frontend({
                "type": "error",
                "vault_id": vault_id,
                "error": error_msg,
                "fund_url": f"https://signetfaucet.com/",
                "wallet_address": wallet.address_str
            })
            return

        # Determine destination
        dest = VAULT_DESTINATION_ADDRESS
        if not dest or dest == "tb1q_YOUR_DESTINATION_ADDRESS":
            # If no destination set, send to self (demonstrates the tx construction)
            dest = wallet.address_str
            print(f"ℹ️  No destination set, sending to self for demonstration")

        # BUILD REAL TRANSACTION
        print(f"🔨 Constructing Bitcoin Signet transaction...")
        print(f"   From:   {wallet.address_str}")
        print(f"   To:     {dest}")
        print(f"   Amount: {COVENANT_PAYOUT_SATS} sats")

        raw_tx = wallet.create_transaction(
            to_address=dest,
            amount_sats=COVENANT_PAYOUT_SATS,
            fee_sats=300
        )
        print(f"📝 Raw TX constructed ({len(raw_tx)//2} bytes)")

        # BROADCAST REAL TRANSACTION
        print(f"📡 Broadcasting to Bitcoin Signet...")
        txid = wallet.broadcast_transaction(raw_tx)

        explorer_url = f"{SIGNET_EXPLORER}/tx/{txid}"
        print(f"\n✅ COVENANT EXECUTED SUCCESSFULLY!")
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
        print(f"❌ Bitcoin TX failed: {error_msg}")
        await notify_frontend({
            "type": "error",
            "vault_id": vault_id,
            "error": error_msg
        })

# --- STARKNET EVENT LISTENER ---
async def starknet_listener():
    global last_block_num

    if DEMO_FORCE:
        print("\n☢️  DEMO_FORCE MODE — Skipping Starknet listener")
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
            print(f"⚠️ First run. Starting from block {last_block_num}")
        except Exception as e:
            print(f"⚠️ Startup failed: {e}. Will retry...")

    print(f"\n👀 Watching Starknet Contract: {REGISTRY_CONTRACT_ADDRESS}")
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
                print(f"\n🚨 PullAuthorized event detected!")
                print(f"   Vault ID: {vault_id}")
                print(f"   Starknet TX: {tx_hash_hex}")

                if vault_id == TARGET_VAULT_ID:
                    await execute_bitcoin_logic(vault_id, starknet_tx_hash=tx_hash_hex)
                else:
                    print(f"   ℹ️ Vault {vault_id} != target {TARGET_VAULT_ID}, skipping")

            last_block_num = latest.block_number
            save_persistence()
            await asyncio.sleep(POLL_INTERVAL_SECS)

        except Exception as e:
            print(f"⚠️ RPC Error: {e}")
            if current_rpc == STARKNET_RPC_PRIMARY:
                current_rpc = STARKNET_RPC_FALLBACK
                print(f"🔄 Switching to fallback: {current_rpc}")
            else:
                current_rpc = STARKNET_RPC_PRIMARY
                print(f"🔄 Switching to primary: {current_rpc}")
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
    print(f"🌍 WebSocket server on port {WS_PORT}")
    print(f"🏥 Health check: http://localhost:{WS_PORT}/health\n")

    await starknet_listener()

if __name__ == "__main__":
    asyncio.run(main())
```

### File: `node/requirements.txt`

```
aiohttp>=3.9.0
starknet-py>=0.28.0
python-bitcoinlib>=0.12.2
requests>=2.31.0
python-dotenv>=1.0.0
```

**System dependency (Linux):** starknet-py requires `libgmp3-dev`:
```bash
sudo apt-get install -y libgmp3-dev build-essential python3-dev
```
**System dependency (macOS):**
```bash
brew install gmp
```

---

## COMPONENT 5: HELPER SCRIPTS

### File: `scripts/setup_wallet.py`

```python
"""
Step 1: Generate a Bitcoin Signet wallet for the Covenant Node.
Run this FIRST before anything else.
"""
import sys
sys.path.insert(0, '../node')
from bitcoin_wallet import SignetWallet

print("🔑 Covenant-CAD Wallet Setup")
print("=" * 50)

wallet = SignetWallet()
wallet.save_to_file("../node/covenant_wallet.json")

print(f"\n✅ Wallet created!")
print(f"\n📋 NEXT STEPS:")
print(f"   1. Go to https://signetfaucet.com/")
print(f"   2. Enter address: {wallet.address_str}")
print(f"   3. Request 0.01 sBTC (free!)")
print(f"   4. Wait ~1-2 minutes for confirmation")
print(f"   5. Run: python check_balance.py")
```

### File: `scripts/check_balance.py`

```python
"""Check Signet wallet balance."""
import sys
sys.path.insert(0, '../node')
from bitcoin_wallet import SignetWallet

wallet = SignetWallet.load_from_file("../node/covenant_wallet.json")
wallet.info()
```

### File: `scripts/register_vault.py`

```python
"""
Register a covenant vault on Starknet Sepolia.
Uses starknet-py to call register_covenant().
"""
import asyncio
import sys
sys.path.insert(0, '../node')
from config import REGISTRY_CONTRACT_ADDRESS, STARKNET_RPC_PRIMARY
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.account.account import Account
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.contract import Contract
from starknet_py.net.client_models import ResourceBounds, ResourceBoundsMapping

# You need to provide your Starknet Sepolia account details
ACCOUNT_ADDRESS = "YOUR_STARKNET_ACCOUNT_ADDRESS"  # Update this
PRIVATE_KEY = "YOUR_STARKNET_PRIVATE_KEY"           # Update this

# Resource bounds for v3 transactions (Sepolia fees are minimal)
RESOURCE_BOUNDS = ResourceBoundsMapping(
    l1_gas=ResourceBounds(max_amount=int(1e5), max_price_per_unit=int(1e13)),
    l2_gas=ResourceBounds(max_amount=int(1e10), max_price_per_unit=int(1e17)),
    l1_data_gas=ResourceBounds(max_amount=int(1e5), max_price_per_unit=int(1e13)),
)

async def main():
    client = FullNodeClient(node_url=STARKNET_RPC_PRIMARY)

    account = Account(
        client=client,
        address=int(ACCOUNT_ADDRESS, 16),
        key_pair=KeyPair.from_private_key(int(PRIVATE_KEY, 16)),
        chain=StarknetChainId.SEPOLIA
    )

    contract = await Contract.from_address(
        address=int(REGISTRY_CONTRACT_ADDRESS, 16),
        provider=account
    )

    # Register vault_id=1 with conditions_hash=0xCAFE
    vault_id = 1
    conditions_hash = 0xCAFE

    print(f"📋 Registering vault {vault_id} with conditions 0x{conditions_hash:X}...")
    invocation = await contract.functions["register_covenant"].invoke_v3(
        vault_id, conditions_hash,
        resource_bounds=RESOURCE_BOUNDS
    )
    await invocation.wait_for_acceptance()
    print(f"✅ Vault registered! TX: {hex(invocation.hash)}")
    print(f"🔍 View: https://sepolia.starkscan.co/tx/{hex(invocation.hash)}")

asyncio.run(main())
```

### File: `scripts/trigger_pull.py`

```python
"""
Trigger execute_pull on Starknet Sepolia.
This fires the PullAuthorized event that the node watches for.
"""
import asyncio
import sys
sys.path.insert(0, '../node')
from config import REGISTRY_CONTRACT_ADDRESS, STARKNET_RPC_PRIMARY
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.account.account import Account
from starknet_py.net.models import StarknetChainId
from starknet_py.net.signer.stark_curve_signer import KeyPair
from starknet_py.contract import Contract
from starknet_py.net.client_models import ResourceBounds, ResourceBoundsMapping

# You need to provide your Starknet Sepolia account details
ACCOUNT_ADDRESS = "YOUR_STARKNET_ACCOUNT_ADDRESS"  # Update this
PRIVATE_KEY = "YOUR_STARKNET_PRIVATE_KEY"           # Update this

# Resource bounds for v3 transactions (Sepolia fees are minimal)
RESOURCE_BOUNDS = ResourceBoundsMapping(
    l1_gas=ResourceBounds(max_amount=int(1e5), max_price_per_unit=int(1e13)),
    l2_gas=ResourceBounds(max_amount=int(1e10), max_price_per_unit=int(1e17)),
    l1_data_gas=ResourceBounds(max_amount=int(1e5), max_price_per_unit=int(1e13)),
)

async def main():
    client = FullNodeClient(node_url=STARKNET_RPC_PRIMARY)

    account = Account(
        client=client,
        address=int(ACCOUNT_ADDRESS, 16),
        key_pair=KeyPair.from_private_key(int(PRIVATE_KEY, 16)),
        chain=StarknetChainId.SEPOLIA
    )

    contract = await Contract.from_address(
        address=int(REGISTRY_CONTRACT_ADDRESS, 16),
        provider=account
    )

    vault_id = 1
    # Proof and public_inputs — these are real arrays passed to the verifier
    proof = [42, 123, 456]          # Non-empty proof (verifier checks this)
    public_inputs = [0xCAFE]        # Non-empty public inputs (verifier checks this)

    print(f"🚀 Triggering execute_pull for vault {vault_id}...")
    print(f"   Proof: {proof}")
    print(f"   Public inputs: {public_inputs}")

    invocation = await contract.functions["execute_pull"].invoke_v3(
        vault_id, proof, public_inputs,
        resource_bounds=RESOURCE_BOUNDS
    )
    await invocation.wait_for_acceptance()
    print(f"\n✅ PullAuthorized event emitted!")
    print(f"   TX: {hex(invocation.hash)}")
    print(f"   Explorer: https://sepolia.starkscan.co/tx/{hex(invocation.hash)}")
    print(f"\n   The Covenant Node should now detect this and broadcast a Bitcoin Signet TX!")

asyncio.run(main())
```

---

## COMPONENT 6: VISUALIZER UI

### File: `ui/index.html`

**Single HTML file. All CSS and JS inline. No React, no build step.**

> ⚠️ **DESIGN MANDATE — READ THIS BEFORE WRITING ANY CSS**
>
> This UI will be projected on a big screen at a hackathon demo. It must look like a hand-crafted,
> intentionally designed product — NOT a generic AI-generated dashboard. No purple-on-white gradients.
> No Inter/Roboto/Arial. No rounded cards with drop shadows on a flat white background. No cookie-cutter
> "startup SaaS" aesthetic. Follow every instruction below precisely.

---

### AESTHETIC DIRECTION: "Cyberpunk Control Room meets Bloomberg Terminal"

The vibe is: you're looking at a mission control dashboard for a cross-chain vault protocol. It should
feel like a mix between a **Bloomberg terminal** (dense, information-rich, monospaced data) and a
**sci-fi movie control panel** (glowing accents, dark atmosphere, purposeful animations). Think the
UI from the movie *Interstellar*'s spacecraft displays, not a generic Tailwind landing page.

---

### TYPOGRAPHY (Critical — this is the #1 giveaway of AI-generated sites)

**DO NOT** use Inter, Roboto, Arial, system-ui, or Space Grotesk. These are the most overused AI fonts.

Use Google Fonts. Load these two specifically:
- **Display / Headings**: `"IBM Plex Mono"` weight 600 — for titles, vault state labels, section headers.
  This is a distinctive monospaced font with character. It signals "engineering" without looking generic.
- **Body / Data**: `"IBM Plex Sans"` weight 400/500 — for descriptions, paragraphs, labels.
- **Addresses & Hashes**: `"Fira Code"` weight 400 — for all blockchain addresses, tx hashes, hex values.
  Fira Code has programming ligatures that make hex strings look intentional.

```html
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
```

Typography scale (use `rem` units, set `html { font-size: 16px }`):
- Page title "COVENANT-CAD": `2.5rem` IBM Plex Mono 700, letter-spacing: `0.15em`, uppercase
- Section headers: `0.7rem` IBM Plex Sans 600, letter-spacing: `0.2em`, uppercase, muted color
- Vault state label: `1.8rem` IBM Plex Mono 600
- Data values (addresses, hashes): `0.85rem` Fira Code 400
- Body text: `0.9rem` IBM Plex Sans 400
- Small labels: `0.65rem` IBM Plex Sans 500, uppercase, letter-spacing `0.15em`

---

### COLOR PALETTE (Precise hex values — do not deviate)

The palette is dark and atmospheric with sharp, intentional accents. NOT just "dark mode with green".

```css
:root {
    /* ── Background layers (from deepest to surface) ── */
    --bg-void: #06080c;          /* Deepest background — near-black with cold blue undertone */
    --bg-base: #0b0f18;          /* Main page background */
    --bg-surface: #111827;       /* Card/panel backgrounds */
    --bg-elevated: #1a2234;      /* Elevated elements, hover states */
    --bg-input: #0d1220;         /* Input fields, code blocks */

    /* ── Borders ── */
    --border-subtle: #1e293b;    /* Barely visible panel borders */
    --border-active: #334155;    /* Active/focused borders */

    /* ── Text hierarchy ── */
    --text-primary: #e2e8f0;     /* Main text — warm off-white, NOT pure #fff */
    --text-secondary: #8892a4;   /* Labels, secondary info — desaturated blue-gray */
    --text-muted: #4a5568;       /* Timestamps, hints — very muted */
    --text-dim: #2d3748;         /* Barely-there text for decoration */

    /* ── Accent: Bitcoin Orange ── */
    --btc-orange: #f7931a;       /* The actual Bitcoin brand orange */
    --btc-orange-dim: #f7931a22; /* For glows and backgrounds */
    --btc-orange-muted: #b36a10; /* Darker variant */

    /* ── Accent: Starknet Blue ── */
    --stark-blue: #29aafd;       /* Starknet's brand blue */
    --stark-blue-dim: #29aafd18; /* For glows and backgrounds */
    --stark-blue-muted: #1a7ab8; /* Darker variant */

    /* ── Semantic: States ── */
    --locked-red: #ef4444;       /* Vault locked */
    --locked-glow: #ef444420;
    --unlocking-amber: #f59e0b;  /* Vault unlocking */
    --unlocking-glow: #f59e0b18;
    --success-green: #10b981;    /* Vault unlocked / success */
    --success-glow: #10b98118;
    --error-red: #dc2626;
    --error-glow: #dc262618;

    /* ── Special ── */
    --glow-pulse: #10b98140;     /* For animated pulse rings */
}
```

**IMPORTANT**: The background is NOT flat. Apply a very subtle noise texture and a radial gradient:
```css
body {
    background: var(--bg-base);
    background-image:
        radial-gradient(ellipse at 20% 50%, #29aafd06 0%, transparent 50%),
        radial-gradient(ellipse at 80% 50%, #f7931a06 0%, transparent 50%);
    /* Add a CSS noise overlay via a pseudo-element or inline SVG filter for grain */
}
```

Also add a **very faint grid pattern** to the background using a CSS background-image repeating-linear-gradient — thin 1px lines at `#ffffff04` every 60px. This gives the "control room" feel without being distracting.

---

### LAYOUT (Asymmetric, Dense, Not Generic)

**DO NOT** center everything in a max-width container with equal padding like a typical landing page.

The layout should be a **dashboard grid** — dense and information-rich:

```
┌─────────────────────────────────────────────────────────────────┐
│  COVENANT-CAD              [mode badge]     [connection status] │  ← Minimal top bar
├──────────────────────────┬──────────────────────────────────────┤
│                          │                                      │
│   ARCHITECTURE FLOW      │       VAULT STATE                   │
│   ┌──────┐  ┌──────┐    │       (giant central display)       │
│   │Brain │→ │ Hand │→   │                                      │
│   └──────┘  └──────┘    │       🔒 LOCKED                     │
│        ↓                 │       ──────────                     │
│   ┌──────┐               │       vault_id: 1                   │
│   │Vault │               │       conditions: 0xCAFE            │
│   └──────┘               │                                      │
│                          │                                      │
├──────────────────────────┼──────────────────────────────────────┤
│  NETWORK DETAILS         │  EVENT LOG                           │
│  ├ Starknet: 0x1234...   │  12:34:05 Connected to node         │
│  ├ Bitcoin:  tb1q89ab...  │  12:34:08 Watching vault #1         │
│  ├ Balance:  4,200 sats  │  12:35:12 PullAuthorized detected!  │
│  └ Verifier: 0x5678...   │  12:35:14 Broadcasting to Signet... │
├──────────────────────────┼──────────────────────────────────────┤
│  TRANSACTION RECEIPT (appears after success, slides up)        │
│  Starknet TX → [link]    Bitcoin TX → [link]   Amount: 1000   │
└─────────────────────────────────────────────────────────────────┘
```

Use CSS Grid (`grid-template-columns: 1fr 1.5fr; grid-template-rows: auto 1fr auto auto;`).
On screens < 900px wide, collapse to single column.

The layout should feel **tight** — use `gap: 1px` between grid cells with `var(--border-subtle)` as
the grid background-color so the 1px gaps act as panel dividers (Bloomberg-terminal style).

---

### PANEL STYLING (Not cards — panels)

**DO NOT** use rounded-corner cards with box-shadows. This is not a SaaS dashboard.

Panels should feel like **terminal panes**:
- `background: var(--bg-surface)`
- `border: 1px solid var(--border-subtle)` — thin, barely visible
- `border-radius: 0px` — **sharp corners, no rounding** (this is deliberate and critical)
- Each panel has a **tiny label** in the top-left corner:
  ```css
  .panel-label {
      font: 500 0.6rem/1 'IBM Plex Sans', sans-serif;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--text-muted);
      padding: 10px 14px 0;
  }
  ```
- Padding inside panels: `14px` — not too roomy, not cramped.

---

### THE ARCHITECTURE FLOW (Left panel — "SYSTEM FLOW")

This is NOT a static image. It's three **connected boxes** built in HTML/CSS:

Each box represents a system component:
- **"BRAIN"** — labeled `STARKNET SEPOLIA`, icon: a small inline SVG of a brain or circuit
- **"HAND"** — labeled `COVENANT NODE`, icon: a small inline SVG of a hand or relay
- **"VAULT"** — labeled `BITCOIN SIGNET`, icon: a small inline SVG of a lock/vault

Box styling:
```css
.arch-box {
    border: 1px solid var(--border-subtle);
    background: var(--bg-input);
    padding: 12px 16px;
    position: relative;
}
.arch-box .label {
    font: 600 0.6rem/1 'IBM Plex Sans';
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 4px;
}
.arch-box .name {
    font: 600 1rem/1.2 'IBM Plex Mono';
    color: var(--text-primary);
}
```

Connectors between boxes: use `::after` pseudo-elements or small divs with dashed borders and
animated `background-position` (moving dashes = data flow animation).

**During UNLOCKING state**: The connector lines animate — the dashes move from Brain → Hand → Vault
using `@keyframes` with `background-position` animation on a `repeating-linear-gradient`.
Each box gets a subtle glowing border matching its accent color (`--stark-blue` for Brain,
`--text-secondary` for Hand, `--btc-orange` for Vault).

**During SUCCESS state**: All three boxes get a brief `--success-green` border-flash animation,
then settle to their normal state. The connector lines become solid green briefly.

---

### THE VAULT STATE (Right panel — the hero element)

This is the **largest visual element** on the page. It should command attention.

**Structure:**
- A large vault ID display: `VAULT #1` in `IBM Plex Mono` 600, 1.2rem, muted
- Below it: the **state indicator** — this is the hero:

**LOCKED state:**
```css
.vault-state-locked {
    /* Large lock icon — use an inline SVG, NOT an emoji */
    /* Below the icon: */
    /* Text: "LOCKED" in IBM Plex Mono 700, 1.8rem */
    /* Color: var(--locked-red) */
    /* Add a subtle pulsing glow ring around the icon using box-shadow animation */
    /* box-shadow: 0 0 0 0 var(--locked-glow); animation: pulse-ring 3s ease infinite; */
}
```

**UNLOCKING state:**
```css
.vault-state-unlocking {
    /* Animated: the lock icon rotates slightly and shakes */
    /* Text: "VERIFYING PROOF..." in IBM Plex Mono, var(--unlocking-amber) */
    /* Below: "Starknet → Verifier → Node → Signet" with each word lighting up sequentially */
    /* Add a spinning ring animation around the icon (CSS border-spinner, not a GIF) */
    /* The entire panel gets a faint amber glow: box-shadow inset */
}
```
For the sequential word lighting, use staggered `animation-delay` on each span:
```css
.step-word { color: var(--text-muted); transition: color 0.5s; }
.step-word.active { color: var(--unlocking-amber); }
```
Cycle through them with a JS `setInterval` every 800ms.

**UNLOCKED state (SUCCESS):**
```css
.vault-state-unlocked {
    /* Lock icon morphs to an unlocked padlock (swap SVG) */
    /* Text: "UNLOCKED" in IBM Plex Mono 700, var(--success-green) */
    /* Below: the Bitcoin TX hash in Fira Code, clickable, with a subtle green underline */
    /* The TX hash should have a "copy" icon next to it */
    /* Explorer link: "View on mempool.space →" as a small link below */
    /* Entrance animation: scale from 0.95 to 1.0, opacity 0 to 1, 0.4s ease-out */
    /* Celebration: a single subtle ring-pulse in green, then done. NO confetti, NO particles */
}
```

**ERROR state:**
```css
.vault-state-error {
    /* Text: "ERROR" in red */
    /* Error message below in smaller text */
    /* If it's a funding error: show the wallet address in Fira Code with a "Copy" button */
    /* and a direct link to the faucet */
}
```

---

### NETWORK DETAILS PANEL (Bottom-left)

A **dense info table** — NOT a list of cards.

```
NETWORK DETAILS
─────────────────────────────────────
Starknet    0x1a2b...3c4d    Sepolia
Bitcoin     tb1qxy...89ab    Signet
Balance     4,200 sats       ●
Verifier    0x5678...9abc    Sepolia
─────────────────────────────────────
```

Each row is a `display: flex` with three columns: label (muted), value (Fira Code, primary), network tag.
Addresses are **truncated** with JS: show first 6 chars + `...` + last 4 chars.
Full address shown on hover via `title` attribute AND a small tooltip.
Each address is clickable → opens explorer in new tab.
The balance dot `●` is green if > 1000 sats, amber if < 1000, red if 0.

Use a real top-border as the divider: `border-top: 1px solid var(--border-subtle)` on each row.

---

### EVENT LOG (Bottom-right)

Styled like a **real terminal log**, not a chat widget:

```css
.event-log {
    font: 400 0.78rem/1.6 'Fira Code', monospace;
    color: var(--text-secondary);
    background: var(--bg-input);
    overflow-y: auto;
    max-height: 200px;
    padding: 10px 14px;
    /* Custom scrollbar: thin, matching border-subtle color */
}
.event-log::-webkit-scrollbar { width: 4px; }
.event-log::-webkit-scrollbar-thumb { background: var(--border-active); }
```

Each log entry format:
```
[12:34:05] Connected to Covenant Node
[12:34:08] Watching vault #1 on Starknet Sepolia
[12:35:12] ▸ PullAuthorized event detected — TX: 0x1a2b...
[12:35:14] ▸ Constructing Bitcoin Signet transaction...
[12:35:16] ✓ Broadcast successful — TXID: abc123...
```

Timestamps in `var(--text-dim)`. Normal text in `var(--text-secondary)`.
Lines starting with `▸` (events) in `var(--stark-blue)`.
Lines starting with `✓` (success) in `var(--success-green)`.
Lines starting with `✗` (errors) in `var(--error-red)`.

New entries should scroll into view automatically. Add each entry with a `fadeInUp` animation
(translateY(4px) → 0, opacity 0 → 1, 200ms).

---

### TRANSACTION RECEIPT (Appears on success — slides up from bottom of vault panel)

This section is **hidden by default** and slides up with a CSS transition when a transaction succeeds.

```css
.tx-receipt {
    background: var(--bg-elevated);
    border-top: 1px solid var(--success-green);  /* Green top accent line */
    padding: 16px;
    transform: translateY(20px);
    opacity: 0;
    transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.tx-receipt.visible {
    transform: translateY(0);
    opacity: 1;
}
```

Contents — a two-column grid:
```
TRANSACTION RECEIPT
──────────────────────────────────────────
Starknet TX    0x1a2b...3c4d  [↗ Starkscan]
Bitcoin TX     abc123...def4  [↗ mempool.space]
Amount         1,000 sats
Destination    tb1qxy...89ab
Timestamp      2025-02-25 14:35:16 UTC
──────────────────────────────────────────
```

The `[↗ Starkscan]` and `[↗ mempool.space]` are small links (0.7rem, uppercase) in their respective
accent colors (`--stark-blue` and `--btc-orange`).

---

### MODE BADGE (Top-right of header bar)

Not a generic pill — a **status indicator with purpose**:

```css
.mode-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font: 500 0.65rem/1 'IBM Plex Sans';
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 6px 14px;
    border: 1px solid;
}

/* LIVE mode */
.mode-badge.live {
    color: var(--success-green);
    border-color: var(--success-green);
    background: var(--success-glow);
}
.mode-badge.live::before {
    content: '';
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--success-green);
    animation: blink 2s ease infinite;
}

/* DEMO mode */
.mode-badge.demo {
    color: var(--unlocking-amber);
    border-color: var(--unlocking-amber);
    background: var(--unlocking-glow);
}

/* DISCONNECTED */
.mode-badge.disconnected {
    color: var(--error-red);
    border-color: var(--error-red);
    background: var(--error-glow);
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}
```

---

### SVG ICONS (Inline, not emoji — emoji look unprofessional on projectors)

Create simple inline SVGs for:
- **Lock icon** (locked padlock) — 24x24, stroke-only, `stroke: currentColor`, `stroke-width: 1.5`
- **Unlock icon** (open padlock) — same style
- **Brain/circuit icon** — for Starknet (simple circuit-like lines)
- **Relay/arrows icon** — for the Node
- **Vault/safe icon** — for Bitcoin
- **External link icon** — small `↗` arrow for explorer links
- **Copy icon** — small clipboard for address copy
- **Checkmark** — for success states
- **Warning triangle** — for errors

Style all SVGs with `currentColor` so they inherit the text color. Size: 16-24px depending on context.

---

### ANIMATIONS (Purposeful, not decorative)

Only animate things that communicate **state changes**:

1. **Vault state transition** — when state changes, the vault icon/text fades out (100ms), then the new
   state fades in (300ms). Use a CSS class swap with `transition: opacity 0.3s, transform 0.3s`.

2. **Architecture flow pulse** — during UNLOCKING, the connector lines animate (dashes move). Each
   component box lights up sequentially (Brain → 400ms delay → Hand → 400ms delay → Vault) using
   `animation-delay`. This creates a visual "data flowing through the system" effect.

3. **Receipt slide-up** — the transaction receipt slides up from below (translateY + opacity transition).

4. **Log entry fade** — new log entries fade in from below (subtle, fast, 200ms).

5. **Balance dot pulse** — the balance indicator dot gently pulses when balance changes.

**DO NOT add**: page load animations on every element, floating particles, parallax, confetti,
morphing blobs, gradient animations, or any "wow factor" animation that doesn't communicate system state.

---

### WEBOCKET CONNECTION (JS Requirements)

```javascript
// Connection to node
const WS_URL = 'ws://localhost:8080/ws';
let ws;
let reconnectTimer;

function connect() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        clearTimeout(reconnectTimer);
        updateConnectionStatus('connected');
        addLogEntry('Connected to Covenant Node', 'info');
    };

    ws.onclose = () => {
        updateConnectionStatus('disconnected');
        addLogEntry('Connection lost. Reconnecting...', 'error');
        reconnectTimer = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
        ws.close();
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
}

function handleMessage(data) {
    switch (data.type) {
        case 'status':
            // Update mode badge, wallet address, balance, contract address
            // Set vault state to LOCKED
            // Populate network details panel
            // Store explorer URLs for later use
            break;
        case 'unlocking':
            // Transition vault to UNLOCKING state
            // Start architecture flow animation
            // Log the Starknet TX hash
            break;
        case 'success':
            // Transition vault to UNLOCKED state
            // Show transaction receipt with real explorer links
            // Stop architecture flow animation, show success flash
            // Display clickable TX hash: data.explorer_url
            break;
        case 'error':
            // Transition vault to ERROR state
            // Show error message
            // If funding error: show wallet address + faucet link
            break;
    }
}
```

**Message types the UI must handle** (these come from the Python node):
```json
{"type": "status", "msg": "...", "vault_state": "LOCKED", "wallet_address": "...", "wallet_balance_sats": 0, "starknet_contract": "0x...", "explorer_starknet": "...", "explorer_bitcoin": "..."}
{"type": "unlocking", "vault_id": 1, "starknet_tx": "0x...", "starknet_url": "..."}
{"type": "success", "vault_id": 1, "tx_hash": "real_txid", "explorer_url": "https://mempool.space/signet/tx/...", "starknet_tx": "0x...", "amount_sats": 1000, "destination": "tb1q..."}
{"type": "error", "vault_id": 1, "error": "...", "fund_url": "...", "wallet_address": "..."}
```

---

### ADDRESS UTILITIES (JS)

```javascript
// Truncate long addresses for display
function truncateAddress(addr, startChars = 6, endChars = 4) {
    if (!addr || addr.length <= startChars + endChars + 3) return addr;
    return `${addr.slice(0, startChars)}...${addr.slice(-endChars)}`;
}

// Copy to clipboard with visual feedback
function copyToClipboard(text, element) {
    navigator.clipboard.writeText(text).then(() => {
        element.classList.add('copied');
        setTimeout(() => element.classList.remove('copied'), 1500);
    });
}
```

---

### RESPONSIVE BEHAVIOR

- **≥ 1200px**: Full dashboard grid as shown above. This is the "projector demo" layout.
- **900–1199px**: Architecture flow moves above vault state (stacks vertically in the main area).
- **< 900px**: Single column. Everything stacks. Network details become a horizontal scroll row.
  Vault state remains the hero element.

---

### WHAT THE FINAL RESULT MUST LOOK LIKE

When a judge sees this UI projected at a demo, they should think:
1. "This team actually designed their UI" — because of the intentional typography, the Bloomberg-terminal
   density, the sharp corners, the ambient background treatment.
2. "This is a real system" — because every address links to a real explorer, the balance updates in
   real-time, and the log shows actual system activity.
3. "The demo flow is clear" — because the vault state transition is the unmistakable hero moment:
   LOCKED (red, tense) → UNLOCKING (amber, animated, exciting) → UNLOCKED (green, satisfying,
   with proof — a real Bitcoin TX hash they can click).

**The single most important visual moment**: when the vault unlocks and the real Bitcoin transaction
hash appears with a clickable link to mempool.space. That's the money shot. Make it feel earned.

---

## COMPONENT 7: README.md

Create a comprehensive README with:

1. **Title**: `# Covenant-CAD 🔐⚡` with subtitle
2. **Badges**: "Built on Starknet Sepolia" + "Bitcoin Signet" + "Zero Cost"
3. **One-liner description**
4. **Trust Model** (exact text from architecture section)
5. **Architecture diagram** (Mermaid format)
6. **How it works** (numbered steps matching the real flow)
7. **Tech Stack**: Cairo/Starknet Sepolia, Python (starknet-py, python-bitcoinlib, aiohttp), Bitcoin Signet, Blockstream Esplora API
8. **Quick Start** (step-by-step from zero to demo)
9. **Cost**: ZERO — explain all testnet faucets
10. **Security features**: Vault existence check, replay protection, real verifier contract call, selector assertion, atomic persistence, RPC failover, API failover
11. **Verification**: How judges can verify the real transactions on explorers
12. **Future work**: Full Garaga Groth16 verifier, OP_CAT mainnet, trustless bridge elimination
13. **References**: Links to OP_CAT BIP, Garaga, Starknet docs
14. **License**: MIT

---

## END-TO-END SETUP (Step by Step)

> **FOR CLAUDE CODE**: You should execute every `bash` block below in sequence. When you hit a
> `🖐️ HUMAN ACTION REQUIRED` block, STOP and ask the user to do that step in their browser,
> then wait for them to confirm before continuing. Parse command outputs to extract addresses,
> class hashes etc. and use them in subsequent commands. Write extracted values to a `.env` file
> automatically — do NOT ask the user to copy-paste hex addresses.

---

### Phase 1: Environment Setup

**Claude Code runs all of these:**

```bash
# 1. Install ALL Starknet tools with ONE command (starkup)
# starkup installs: Scarb, Starknet Foundry (sncast+snforge), Starknet Devnet, Universal Sierra Compiler
# Docs: https://docs.starknet.io/guides/quickstart/environment-setup/
# Repo: https://github.com/software-mansion/starkup
curl --proto '=https' --tlsv1.2 -sSf https://sh.starkup.sh | sh

# Source the updated PATH (starkup installs via asdf)
source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true
export PATH="$HOME/.asdf/shims:$HOME/.asdf/bin:$PATH"

# Verify all Starknet tools installed
echo "=== Starknet Tool Verification ==="
scarb --version && echo "✅ Scarb OK" || echo "❌ Scarb MISSING"
sncast --version && echo "✅ sncast OK" || echo "❌ sncast MISSING"
snforge --version && echo "✅ snforge OK" || echo "❌ snforge MISSING"
echo "=== Done ==="
```

```bash
# 2. Install Python system dependencies (required by starknet-py)
# starknet-py needs libgmp for fast elliptic curve operations
sudo apt-get update && sudo apt-get install -y libgmp3-dev build-essential python3-dev 2>/dev/null \
  || brew install gmp 2>/dev/null \
  || echo "⚠️ Could not auto-install libgmp. Install manually if starknet-py fails."

# 3. Install Python dependencies
cd node
pip install -r requirements.txt
cd ..
```

```bash
# 4. Verify all tools are available
echo "=== Full Tool Verification ==="
scarb --version && echo "✅ Scarb OK" || echo "❌ Scarb MISSING"
sncast --version && echo "✅ sncast OK" || echo "❌ sncast MISSING"
snforge --version && echo "✅ snforge OK" || echo "❌ snforge MISSING"
python3 -c "import starknet_py; print('✅ starknet-py OK')" || echo "❌ starknet-py MISSING"
python3 -c "import bitcoin; print('✅ python-bitcoinlib OK')" || echo "❌ python-bitcoinlib MISSING"
python3 -c "import aiohttp; print('✅ aiohttp OK')" || echo "❌ aiohttp MISSING"
python3 -c "import dotenv; print('✅ python-dotenv OK')" || echo "❌ python-dotenv MISSING"
echo "=== Done ==="
```

---

### Phase 2: Build Cairo Contracts

**Claude Code runs:**

```bash
cd contracts
scarb build
echo "=== Build Artifacts ==="
ls -la target/dev/*.contract_class.json
echo "=== Done ==="
# Expected: Two files:
#   covenant_cad_SimpleVerifier.contract_class.json
#   covenant_cad_CovenantRegistry.contract_class.json
cd ..
```

---

### Phase 3: Create Starknet Sepolia Account

**Claude Code runs:**

```bash
# Create a new Starknet Sepolia account
# This generates a keypair and account address but does NOT deploy yet
sncast account create --name covenant_dev --network sepolia 2>&1 | tee /tmp/sncast_account_create.txt

# Extract the account address from output
# The output format is typically: "Account address: 0x..."
echo ""
echo "============================================="
echo "  STARKNET ACCOUNT CREATED"
echo "============================================="
cat /tmp/sncast_account_create.txt
echo "============================================="
```

After running the above, **parse the output** to extract the account address (it starts with `0x`).
Store it in a variable or temp file for use in later steps.

---

### 🖐️ HUMAN ACTION REQUIRED: Fund Starknet Account

**STOP HERE. Tell the user:**

> Your Starknet Sepolia account has been created.
>
> **You need to fund it (FREE — takes 30 seconds):**
>
> 1. Open your browser and go to: **https://starknet-faucet.vercel.app/**
> 2. Paste this account address: `<ACCOUNT_ADDRESS_FROM_ABOVE>`
> 3. Click "Send" or complete any captcha
> 4. Wait ~30 seconds for the transaction to confirm
>
> **Alternative faucets** (if the primary is down):
> - https://www.alchemy.com/faucets/starknet-sepolia
> - https://learnweb3.io/faucets/starknet_sepolia/
>
> Tell me when you've funded it and I'll continue with deployment.

**Wait for user confirmation before proceeding.**

---

### Phase 4: Deploy Starknet Account

**Claude Code runs (only after user confirms faucet funding):**

```bash
# Deploy the funded account on-chain
sncast account deploy --name covenant_dev --network sepolia 2>&1 | tee /tmp/sncast_account_deploy.txt

echo ""
echo "============================================="
echo "  ACCOUNT DEPLOYED"
echo "============================================="
cat /tmp/sncast_account_deploy.txt
echo "============================================="
```

---

### Phase 5: Deploy SimpleVerifier Contract

**Claude Code runs:**

```bash
# Step 1: Declare the SimpleVerifier class
cd contracts
sncast --account covenant_dev declare \
    --contract-name SimpleVerifier \
    --network sepolia 2>&1 | tee /tmp/sncast_declare_verifier.txt

echo ""
echo "============================================="
echo "  VERIFIER DECLARED"
echo "============================================="
cat /tmp/sncast_declare_verifier.txt
echo "============================================="
cd ..
```

**Parse the output** to extract the `class_hash` (hex string starting with `0x`).
Then immediately run:

```bash
# Step 2: Deploy SimpleVerifier instance (no constructor args)
cd contracts
sncast --account covenant_dev deploy \
    --class-hash <VERIFIER_CLASS_HASH_FROM_ABOVE> \
    --network sepolia 2>&1 | tee /tmp/sncast_deploy_verifier.txt

echo ""
echo "============================================="
echo "  VERIFIER DEPLOYED"
echo "============================================="
cat /tmp/sncast_deploy_verifier.txt
echo "============================================="
cd ..
```

**Parse the output** to extract the deployed `contract_address`. This is `VERIFIER_ADDRESS`.
Store it — you'll need it for the next step AND for the `.env` file.

---

### Phase 6: Deploy CovenantRegistry Contract

**Claude Code runs (using VERIFIER_ADDRESS from Phase 5):**

```bash
# Step 1: Declare the CovenantRegistry class
cd contracts
sncast --account covenant_dev declare \
    --contract-name CovenantRegistry \
    --network sepolia 2>&1 | tee /tmp/sncast_declare_registry.txt

echo ""
echo "============================================="
echo "  REGISTRY DECLARED"
echo "============================================="
cat /tmp/sncast_declare_registry.txt
echo "============================================="
cd ..
```

**Parse output** for `class_hash`, then:

```bash
# Step 2: Deploy CovenantRegistry with verifier address as constructor arg
cd contracts
sncast --account covenant_dev deploy \
    --class-hash <REGISTRY_CLASS_HASH_FROM_ABOVE> \
    --constructor-calldata <VERIFIER_ADDRESS_FROM_PHASE_5> \
    --network sepolia 2>&1 | tee /tmp/sncast_deploy_registry.txt

echo ""
echo "============================================="
echo "  REGISTRY DEPLOYED"
echo "============================================="
cat /tmp/sncast_deploy_registry.txt
echo "============================================="
cd ..
```

**Parse output** for deployed `contract_address`. This is `REGISTRY_ADDRESS`.

---

### Phase 7: Verify Deployment (Sanity Check)

**Claude Code runs:**

```bash
# Verify the verifier address is correctly stored in registry
sncast --account covenant_dev call \
    --contract-address <REGISTRY_ADDRESS> \
    --function get_verifier_address \
    --network sepolia

# Expected output: should match VERIFIER_ADDRESS from Phase 5
```

```bash
# Verify contract is queryable (vault 1 should not exist yet)
sncast --account covenant_dev call \
    --contract-address <REGISTRY_ADDRESS> \
    --function get_covenant \
    --calldata 1 \
    --network sepolia

# Expected output: 0x0 (vault not registered yet)
```

---

### Phase 8: Write .env File Automatically

**Claude Code creates the .env file using all extracted addresses:**

```bash
# Claude Code: write the .env file with all values collected so far
cat > node/.env << 'ENVFILE'
# === Starknet Sepolia (FREE testnet) ===
STARKNET_RPC_PRIMARY=https://starknet-sepolia.public.blastapi.io
STARKNET_RPC_FALLBACK=https://free-rpc.nethermind.io/sepolia-juno

# === Contract Addresses (deployed in Phases 5-6) ===
REGISTRY_CONTRACT_ADDRESS=<REGISTRY_ADDRESS>
VERIFIER_CONTRACT_ADDRESS=<VERIFIER_ADDRESS>

# === Bitcoin Signet (FREE testnet) ===
WALLET_FILE=covenant_wallet.json
VAULT_DESTINATION_ADDRESS=
COVENANT_PAYOUT_SATS=1000

# === Node Settings ===
TARGET_VAULT_ID=1
WS_PORT=8080
POLL_INTERVAL_SECS=3
DEMO_FORCE=0
ENVFILE

echo "✅ .env file written to node/.env"
cat node/.env
```

**IMPORTANT**: Replace `<REGISTRY_ADDRESS>` and `<VERIFIER_ADDRESS>` with the actual hex addresses
parsed from deployment outputs. Do NOT leave placeholders.

---

### Phase 9: Create Bitcoin Signet Wallet

**Claude Code runs:**

```bash
cd scripts
python3 setup_wallet.py 2>&1 | tee /tmp/btc_wallet_setup.txt

echo ""
echo "============================================="
echo "  BITCOIN SIGNET WALLET CREATED"
echo "============================================="
cat /tmp/btc_wallet_setup.txt
echo "============================================="
cd ..
```

**Parse the output** to extract the Bitcoin Signet address (starts with `tb1`).

---

### 🖐️ HUMAN ACTION REQUIRED: Fund Bitcoin Signet Wallet

**STOP HERE. Tell the user:**

> Your Bitcoin Signet wallet has been created.
>
> **You need to fund it with free testnet coins (takes 1-2 minutes):**
>
> 1. Open your browser and go to: **https://signetfaucet.com/**
> 2. Paste this address: `<SIGNET_ADDRESS_FROM_ABOVE>`
> 3. Enter amount: `0.01` (or whatever the faucet allows, 0.001 minimum)
> 4. Submit and wait 1-2 minutes for confirmation
>
> **Alternative faucet** (if primary is down):
> - https://signet.bc-2.jp
>
> Tell me when you've funded it and I'll verify the balance.

**Wait for user confirmation before proceeding.**

---

### Phase 10: Verify Bitcoin Balance

**Claude Code runs (only after user confirms faucet funding):**

```bash
cd scripts
python3 check_balance.py

# Expected: Non-zero balance (at least 1000+ sats)
# If balance is 0, tell user to wait longer or try faucet again
cd ..
```

If balance is 0, tell the user the faucet transaction may still be confirming and to wait another
minute, then re-run `check_balance.py`.

---

### Phase 11: Register a Test Vault on Starknet

**Claude Code runs:**

```bash
# Register vault_id=1 with conditions_hash=0xCAFE
sncast --account covenant_dev invoke \
    --contract-address <REGISTRY_ADDRESS> \
    --function register_covenant \
    --calldata 1 0xCAFE \
    --network sepolia 2>&1 | tee /tmp/register_vault.txt

echo ""
echo "============================================="
echo "  VAULT REGISTERED"
echo "============================================="
cat /tmp/register_vault.txt
echo "============================================="
```

```bash
# Verify vault was registered
sncast --account covenant_dev call \
    --contract-address <REGISTRY_ADDRESS> \
    --function get_covenant \
    --calldata 1 \
    --network sepolia

# Expected: 0xCAFE (51966 in decimal)
```

---

### Phase 12: Start the System (3 Processes)

**Claude Code runs in separate terminals / background processes:**

```bash
# Terminal 1: Start the Covenant Node
cd node
python3 covenant_node.py &
NODE_PID=$!
echo "Node started with PID: $NODE_PID"

# Wait for node to be ready
sleep 3

# Verify node is healthy
curl -s http://localhost:8080/health | python3 -m json.tool
```

```bash
# Terminal 2: Start the UI server
cd ui
python3 -m http.server 8000 &
UI_PID=$!
echo "UI server started with PID: $UI_PID"
echo "🌐 Open in browser: http://localhost:8000/index.html"
```

---

### Phase 13: Trigger the Covenant (The Demo Moment!)

**Claude Code runs:**

```bash
# This fires execute_pull → verifier is called → PullAuthorized event emitted
# The running node will detect it and broadcast a real Bitcoin Signet transaction
sncast --account covenant_dev invoke \
    --contract-address <REGISTRY_ADDRESS> \
    --function execute_pull \
    --calldata 1 3 42 123 456 1 0xCAFE \
    --network sepolia 2>&1 | tee /tmp/trigger_pull.txt
# Calldata breakdown:
#   1         = vault_id
#   3         = proof array length
#   42 123 456 = proof elements (non-empty, verifier checks this)
#   1         = public_inputs array length
#   0xCAFE    = public_inputs[0] (non-empty, verifier checks this)

echo ""
echo "============================================="
echo "  EXECUTE_PULL TRIGGERED"
echo "============================================="
cat /tmp/trigger_pull.txt
echo "============================================="
echo ""
echo "👀 Now watch the node terminal — it should detect the event"
echo "   and broadcast a real Bitcoin Signet transaction!"
echo "🌐 Check UI at http://localhost:8000/index.html"
```

After this, the node should:
1. Detect the PullAuthorized event
2. Construct a real Bitcoin Signet transaction
3. Broadcast it via Blockstream Esplora API
4. Print the real TXID
5. Send it to the UI via WebSocket

```bash
# Verify: Wait a few seconds then check node output and health
sleep 10
curl -s http://localhost:8080/health | python3 -m json.tool
# processed_count should now be 1
```

---

### Emergency Demo (No Network at Venue)

```bash
cd node
DEMO_FORCE=1 python3 covenant_node.py
# Will auto-trigger after 5 seconds
# Bitcoin TX will still be REAL if wallet has funds
# UI will show ⚠️ OFFLINE DEMO MODE badge
```

---

### Cleanup (After Demo)

```bash
# Stop background processes
kill $NODE_PID 2>/dev/null
kill $UI_PID 2>/dev/null
echo "✅ Processes stopped"
```

---

## MANUAL STEPS SUMMARY (Only 2 Browser Actions Required)

| Step | What | Who | Why can't it be automated? |
|------|------|-----|---------------------------|
| Phase 3 faucet | Fund Starknet account | 🖐️ User (browser) | Captcha / anti-bot on faucet website |
| Phase 9 faucet | Fund Bitcoin Signet wallet | 🖐️ User (browser) | Captcha / anti-bot on faucet website |
| **Everything else** | **All commands** | **🤖 Claude Code (terminal)** | **Fully automatable** |

Claude Code handles: tool installation, contract compilation, contract declaration, contract deployment,
address extraction, `.env` file generation, wallet creation, balance checks, vault registration,
system startup, and covenant triggering. The user only opens two faucet websites in their browser.
```

---

## END-TO-END TEST PLAN

### Test 1: Cairo Compilation
```bash
cd contracts && scarb build
# ✅ PASS: No errors, two .contract_class.json files in target/dev/
```

### Test 2: Cairo Unit Tests
Create `contracts/tests/test_contracts.cairo` with tests for:
- `test_register_and_read`: Register vault, read back conditions_hash
- `test_unknown_vault_fails`: execute_pull on unregistered vault → panic 'UNKNOWN_VAULT'
- `test_replay_protection`: execute_pull twice → panic 'VAULT_ALREADY_SPENT'
- `test_duplicate_registration_fails`: register same vault_id twice → panic 'VAULT_ALREADY_EXISTS'
- `test_zero_conditions_fails`: register with conditions_hash=0 → panic 'INVALID_CONDITIONS'
```bash
snforge test
# ✅ PASS: All tests pass
```

### Test 3: Contract Deployment
```bash
# Declare + deploy both contracts
# ✅ PASS: Both addresses returned, verifiable on https://sepolia.starkscan.co/
```

### Test 4: Verifier is Actually Called
```bash
# Call execute_pull with empty proof (should fail at verifier level)
sncast --account covenant_dev invoke \
    --contract-address <REGISTRY> \
    --function execute_pull \
    --calldata 1 0 0 \
    --network sepolia
# ✅ PASS: Transaction REVERTS with 'EMPTY_PROOF' (from verifier, proving it's called)
```

### Test 5: Bitcoin Wallet Creation
```bash
cd scripts && python setup_wallet.py
# ✅ PASS: covenant_wallet.json created with valid Signet address (starts with tb1)
```

### Test 6: Bitcoin Wallet Funding
```bash
# Fund via faucet, then:
python check_balance.py
# ✅ PASS: Balance > 0 sats
```

### Test 7: Node Startup
```bash
cd node && python covenant_node.py
# ✅ PASS: Shows banner with contract address, wallet address, balance
# Shows "Watching Starknet Contract" message
```

### Test 8: Health Endpoint
```bash
curl http://localhost:8080/health | python -m json.tool
# ✅ PASS: Returns JSON with status, mode, wallet info, balance
```

### Test 9: UI WebSocket Connection
```bash
# Open http://localhost:8000/index.html
# ✅ PASS: Shows "🟢 LIVE", wallet address, balance, contract address
```

### Test 10: Full Flow — Register + Trigger + Bitcoin TX
```bash
# 1. Register vault (Terminal 3)
sncast invoke ... register_covenant ... 1 0xCAFE

# 2. Trigger pull (Terminal 3)
sncast invoke ... execute_pull ... (with proof and public_inputs)

# 3. Watch node (Terminal 1)
# ✅ PASS: Node prints "🚨 PullAuthorized event detected!"
# ✅ PASS: Node prints "🔨 Constructing Bitcoin Signet transaction..."
# ✅ PASS: Node prints "✅ Transaction broadcast to Signet! TXID: <real_txid>"

# 4. Check UI (Browser)
# ✅ PASS: Vault transitions LOCKED → UNLOCKING → UNLOCKED
# ✅ PASS: Real TX hash displayed with clickable link

# 5. Verify on explorer
# Open: https://mempool.space/signet/tx/<txid>
# ✅ PASS: Real transaction visible on block explorer
```

### Test 11: Replay Protection
```bash
# Try execute_pull again with same vault_id
sncast invoke ... execute_pull ... 1 ...
# ✅ PASS: Transaction REVERTS with 'VAULT_ALREADY_SPENT'
```

### Test 12: RPC Failover
```bash
# Set PRIMARY_RPC to invalid URL in .env, restart node
# ✅ PASS: Node prints "Switching to fallback" and continues working
```

### Test 13: Persistence
```bash
# Run node, let it process events
# Kill node (Ctrl+C)
# Check node_state.json exists
# Restart node
# ✅ PASS: Resumes from last block, doesn't reprocess old events
```

### Test 14: DEMO_FORCE Mode
```bash
DEMO_FORCE=1 python covenant_node.py
# ✅ PASS: Auto-triggers after 5 seconds
# ✅ PASS: Real Bitcoin TX broadcast (if wallet has funds)
# ✅ PASS: UI shows ⚠️ OFFLINE DEMO MODE badge
```

### Test 15: Empty Wallet Error Handling
```bash
# With empty wallet, trigger execute_pull
# ✅ PASS: Node prints clear error with faucet URL
# ✅ PASS: UI shows error with funding instructions
```

---

## REFERENCE RESOURCES

### Starknet & Cairo (Free Testnet)
- Starknet Docs: https://docs.starknet.io/
- Cairo Book: https://book.cairo-lang.org/
- Starknet Academy: https://academy.starknet.org/
- Starknet Sepolia Faucet: https://starknet-faucet.vercel.app/
- Sepolia Explorer: https://sepolia.starkscan.co/
- Starknet Foundry: https://foundry-rs.github.io/starknet-foundry/
- OpenZeppelin Cairo: https://github.com/OpenZeppelin/cairo-contracts

### Garaga (ZK Verification)
- Garaga Docs: https://garaga.gitbook.io/garaga
- Scaffold-Garaga: https://github.com/KevinSheeranxyj/scaffold-garaga
- Garaga npm: https://www.npmjs.com/package/garaga
- ZK-SNARK Workshop: https://www.youtube.com/watch?v=TxFLvXvYByM

### Bitcoin Signet (Free Testnet)
- Signet Faucet 1: https://signetfaucet.com/
- Signet Faucet 2: https://signet.bc-2.jp
- Signet Explorer: https://mempool.space/signet/
- Esplora API (Signet): https://blockstream.info/signet/api/
- Esplora API Docs: https://github.com/Blockstream/esplora/blob/master/API.md
- python-bitcoinlib: https://github.com/petertodd/python-bitcoinlib
- Bitcoin Signet Wiki: https://en.bitcoin.it/wiki/Signet

### Python Libraries
- starknet-py: https://starknetpy.readthedocs.io/
- python-bitcoinlib: https://pypi.org/project/python-bitcoinlib/
- aiohttp: https://docs.aiohttp.org/

### Hackathon
- Landing: https://hackathon.starknet.org
- DoraHacks: https://dorahacks.io/hackathon/redefine/detail

---

## DEMO SCRIPT (3 Minutes)

### 0:00 - Hook
"Bitcoin lacks programmable pull payments. We built Covenant-CAD — a working sandbox where covenant logic runs on Starknet and triggers real Bitcoin transactions."

### 0:30 - Architecture
"Three components, all on free testnets. The Brain is a Cairo contract on Starknet Sepolia with a real on-chain verifier. The Hand is a Python node watching for events. The Vault holds real Signet bitcoins."

### 1:00 - Show it's real
"Here's our contract on Starkscan [show explorer]. Here's our Bitcoin wallet on mempool.space [show explorer]. Real contracts, real coins, zero cost."

### 1:30 - Action
"I'm calling execute_pull with a proof. The contract calls the verifier, emits PullAuthorized. Watch the node..."
[Node detects event, constructs transaction, broadcasts]
"Real Bitcoin transaction. Click this link — verify it yourself on mempool.space."

### 2:30 - Closing
"We executed a conditional Bitcoin payment where authorization was entirely defined in Cairo, verified by an on-chain verifier, and settled on Bitcoin Signet. Post-OP_CAT, the Python node disappears — Bitcoin verifies the proof directly."

---

## JUDGE Q&A

**Q: Is this trustless?**
A: "No — explicitly a research prototype. The Python node is a trusted relayer. Post-OP_CAT activation, Bitcoin Script could verify the proof commitment directly, eliminating the node entirely."

**Q: Are these real transactions?**
A: "Yes — both Starknet Sepolia and Bitcoin Signet are real blockchain networks. You can verify every transaction on the block explorers. We use testnet to avoid cost, but the cryptographic operations are identical to mainnet."

**Q: Does the verifier actually run?**
A: "Yes — the registry contract makes a real cross-contract call to our deployed verifier. If you pass an empty proof, the verifier rejects it. Try it — call execute_pull with an empty proof array and it reverts with EMPTY_PROOF."

**Q: Why not use the real Garaga verifier?**
A: "Our verifier implements the same interface as Garaga's Groth16 verifier. Swapping it is a one-line change — just point the constructor at Garaga's deployed address. We chose a simplified verifier for hackathon scope while preserving the integration architecture."

**Q: What does OP_CAT actually enable?**
A: "OP_CAT enables script-level introspection for commitments. Scripts would enforce that a transaction's structure corresponds to what a STARK verifier approved. It doesn't verify proofs directly — it enforces commitments that match verifier outputs."

---

## PRE-FLIGHT CHECKLIST

- [ ] `scarb build` succeeds with zero errors
- [ ] Both contracts deployed on Starknet Sepolia (addresses in .env)
- [ ] Verifier address returned by `get_verifier_address` matches deployed verifier
- [ ] Bitcoin Signet wallet has ≥ 2000 sats (enough for 2 demo transactions)
- [ ] `python covenant_node.py` starts without errors, shows correct addresses
- [ ] `curl localhost:8080/health` returns valid JSON
- [ ] UI connects and shows LIVE status with balance
- [ ] At least one vault registered (vault_id=1)
- [ ] `DEMO_FORCE=1` tested — auto-triggers and broadcasts real TX
- [ ] Full flow tested: register → trigger → event detected → Bitcoin TX → explorer link works
- [ ] Replay protection tested: second execute_pull reverts
- [ ] All explorer links open correctly (Starkscan + mempool.space)
- [ ] Backup demo video recorded and ready