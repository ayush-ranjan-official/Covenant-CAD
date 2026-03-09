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
    COutPoint, lx, b2x, b2lx, CScript,
    CTxWitness, CTxInWitness
)
from bitcoin.core.script import CScriptWitness
from bitcoin.core.script import (
    CScript, OP_DUP, OP_HASH160, OP_EQUALVERIFY, OP_CHECKSIG,
    SignatureHash, SIGHASH_ALL
)
from bitcoin.wallet import CBitcoinSecret, P2WPKHBitcoinAddress, CBitcoinAddress

# Select Signet network
bitcoin.SelectParams('signet')

def _p2wpkh_from_pubkey(pubkey):
    """Create P2WPKH address from a public key."""
    from bitcoin.core import Hash160
    return P2WPKHBitcoinAddress.from_bytes(0, Hash160(pubkey))

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
        self.address = _p2wpkh_from_pubkey(self.public_key)

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
            print(f"Warning: Esplora UTXO fetch failed: {e}, trying mempool.space...")
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

        # Sign each input and build witness
        witnesses = []
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

            # Build witness for this input
            witnesses.append(CTxInWitness(CScriptWitness([sig, self.public_key])))

        # Assign complete witness structure
        tx.wit = CTxWitness(witnesses)

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
                print(f"Transaction broadcast to Signet! TXID: {txid}")
                print(f"View on explorer: https://mempool.space/signet/tx/{txid}")
                return txid
            else:
                error_msg = resp.text
                print(f"Broadcast failed: {error_msg}")
                # Fallback to mempool.space
                return self._broadcast_fallback(raw_tx_hex)
        except Exception as e:
            print(f"Warning: Esplora broadcast failed: {e}, trying fallback...")
            return self._broadcast_fallback(raw_tx_hex)

    def _broadcast_fallback(self, raw_tx_hex: str) -> str:
        """Fallback broadcast via mempool.space Signet API."""
        url = f"{MEMPOOL_BASE}/tx"
        resp = requests.post(url, data=raw_tx_hex, timeout=15)
        if resp.status_code == 200:
            txid = resp.text.strip()
            print(f"[Fallback] Transaction broadcast! TXID: {txid}")
            print(f"View on explorer: https://mempool.space/signet/tx/{txid}")
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
        print(f"Wallet saved to {filepath}")
        print(f"WARNING: Keep this file secret — it contains your private key!")

    @classmethod
    def load_from_file(cls, filepath: str) -> 'SignetWallet':
        """Load wallet from saved file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(private_key_wif=data['private_key_wif'])

    def info(self):
        """Print wallet info."""
        balance = self.get_balance()
        print(f"{'='*45}")
        print(f"  Covenant-CAD Bitcoin Signet Wallet")
        print(f"{'='*45}")
        print(f"  Network:  Signet (testnet)")
        print(f"  Address:  {self.address_str}")
        print(f"  Balance:  {balance} sats ({balance/1e8:.8f} sBTC)")
        print(f"  UTXOs:    {len(self.get_utxos())}")
        print(f"{'='*45}")
        if balance == 0:
            print(f"\n  Wallet is empty!")
            print(f"  Get free Signet coins from:")
            print(f"  -> https://signetfaucet.com/")
            print(f"  -> https://signet.bc-2.jp/")
            print(f"  Send to: {self.address_str}")
