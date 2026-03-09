#[starknet::interface]
pub trait ICovenantRegistry<TContractState> {
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
    use starknet::get_block_timestamp;
    use starknet::ContractAddress;
    use starknet::storage::{Map, StoragePointerReadAccess, StoragePointerWriteAccess, StoragePathEntry};

    use super::{IVerifierDispatcher, IVerifierDispatcherTrait};

    #[storage]
    struct Storage {
        covenants: Map<felt252, felt252>,
        authorized_pulls: Map<felt252, bool>,
        verifier_address: ContractAddress,
        owner: ContractAddress,
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
                timestamp: get_block_timestamp(),
            }));
        }
    }
}
