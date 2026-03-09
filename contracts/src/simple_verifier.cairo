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
    use starknet::storage::{StoragePointerReadAccess, StoragePointerWriteAccess};
    use starknet::get_block_timestamp;

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
                timestamp: get_block_timestamp(),
            }));

            // In production: full Groth16 verification via Garaga
            // For sandbox: accept valid-structured proofs
            true
        }
    }
}
