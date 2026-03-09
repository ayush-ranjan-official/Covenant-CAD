# Covenant-CAD Architecture

## Trust Model (Research Prototype)

**Context**: This project simulates Bitcoin OP_CAT capabilities to demonstrate Starknet as an execution layer for Bitcoin covenant logic.

### 1. The Brain (Starknet Sepolia)
Validates covenant conditions, calls an on-chain verifier contract (Garaga-interface-compatible stub), and emits the `PullAuthorized` event upon successful verification.

### 2. The Hand (Covenant Node)
An off-chain Python signer that watches Starknet events and constructs + broadcasts real Bitcoin Signet transactions. Acts as a **Temporary Relayer**.

### 3. The Vault (Bitcoin Signet)
Holds real (testnet) sBTC. Transactions are publicly verifiable on mempool.space/signet.

### Trust Assumptions

**Note**: In this prototype, the Python Node acts as a trusted relayer simulating the future where Bitcoin can verify STARK proofs directly (post-OP_CAT). The verifier contract is a simplified stub implementing the Garaga verifier interface — in production, this would be a full Groth16/STARK verifier.

## System Flow

```
┌──────────────────────────┐     ┌────────────────────────────┐     ┌──────────────────────┐
│   THE BRAIN              │     │   THE HAND                 │     │   THE VAULT           │
│   (Starknet Sepolia)     │────>│   (Covenant Node - Python) │────>│   (Bitcoin Signet)    │
│                          │     │                            │     │                       │
│ - CovenantRegistry.cairo │     │ - Watches PullAuthorized   │     │ - Real sBTC wallet    │
│ - SimpleVerifier.cairo   │     │   events via starknet-py   │     │ - Real UTXO spending  │
│ - Real ZK stub verifier  │     │ - Constructs real Bitcoin  │     │ - Viewable on         │
│ - PullAuthorized event   │     │   Signet transactions      │     │   mempool.space/signet│
│                          │     │ - Broadcasts via Esplora   │     │                       │
│ FREE: Sepolia faucet     │     │   API (no auth needed)     │     │ FREE: Signet faucet   │
└──────────────────────────┘     └────────────────────────────┘     └──────────────────────┘
```

## Contract Architecture

### SimpleVerifier
- Implements `ISimpleVerifier` trait with `verify_groth16(proof, public_inputs) -> bool`
- Validates proof is non-empty and public inputs are non-empty
- Emits `ProofVerified` event for audit trail
- Maintains on-chain verification counter
- Same interface as Garaga — swap is a one-line change

### CovenantRegistry
- `register_covenant(vault_id, conditions_hash)` — registers a vault with conditions
- `execute_pull(vault_id, proof, public_inputs)` — the core function:
  1. Checks vault exists (UNKNOWN_VAULT)
  2. Checks replay protection (VAULT_ALREADY_SPENT)
  3. **Actually calls** the verifier contract via cross-contract dispatch
  4. Marks vault as spent
  5. Emits `PullAuthorized` event

## Security Features

- **Vault existence check**: Cannot execute on unregistered vaults
- **Replay protection**: Each vault can only be spent once
- **Real verifier call**: Cross-contract dispatch to deployed verifier
- **Non-zero validation**: Empty proofs and empty public inputs are rejected
- **Event-based communication**: Node watches real Starknet events
- **Atomic persistence**: Node state saved atomically to prevent corruption
- **RPC failover**: Automatic switch between primary and fallback RPCs
- **API failover**: Bitcoin broadcast falls back to mempool.space if Esplora fails

## Future: Post-OP_CAT

When Bitcoin activates OP_CAT:
1. The Python Node (The Hand) is eliminated entirely
2. Bitcoin Script can verify STARK proof commitments directly
3. The Starknet verifier output is committed to Bitcoin Script
4. OP_CAT enables script-level introspection to enforce the commitment
5. The system becomes fully trustless
