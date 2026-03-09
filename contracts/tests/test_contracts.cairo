use snforge_std::{declare, ContractClassTrait, DeclareResultTrait};
use starknet::ContractAddress;

use covenant_cad::covenant_registry::ICovenantRegistryDispatcher;
use covenant_cad::covenant_registry::ICovenantRegistryDispatcherTrait;

fn deploy_verifier() -> ContractAddress {
    let contract = declare("SimpleVerifier").unwrap().contract_class();
    let (address, _) = contract.deploy(@array![]).unwrap();
    address
}

fn deploy_registry(verifier_address: ContractAddress) -> ContractAddress {
    let contract = declare("CovenantRegistry").unwrap().contract_class();
    let mut calldata = array![];
    calldata.append(verifier_address.into());
    let (address, _) = contract.deploy(@calldata).unwrap();
    address
}

fn setup() -> ICovenantRegistryDispatcher {
    let verifier = deploy_verifier();
    let registry = deploy_registry(verifier);
    ICovenantRegistryDispatcher { contract_address: registry }
}

#[test]
fn test_register_and_read() {
    let registry = setup();

    registry.register_covenant(1, 0xCAFE);

    let conditions = registry.get_covenant(1);
    assert(conditions == 0xCAFE, 'conditions mismatch');

    let is_spent = registry.is_vault_spent(1);
    assert(!is_spent, 'should not be spent');
}

#[test]
#[should_panic(expected: 'UNKNOWN_VAULT')]
fn test_unknown_vault_fails() {
    let registry = setup();

    // Try to execute_pull on vault that was never registered
    registry.execute_pull(999, array![42, 123], array![0xCAFE]);
}

#[test]
#[should_panic(expected: 'VAULT_ALREADY_SPENT')]
fn test_replay_protection() {
    let registry = setup();

    registry.register_covenant(1, 0xCAFE);

    // First pull should succeed
    registry.execute_pull(1, array![42, 123, 456], array![0xCAFE]);

    // Second pull on same vault should fail
    registry.execute_pull(1, array![42, 123, 456], array![0xCAFE]);
}

#[test]
#[should_panic(expected: 'VAULT_ALREADY_EXISTS')]
fn test_duplicate_registration_fails() {
    let registry = setup();

    registry.register_covenant(1, 0xCAFE);

    // Registering same vault_id again should fail
    registry.register_covenant(1, 0xBEEF);
}

#[test]
#[should_panic(expected: 'INVALID_CONDITIONS')]
fn test_zero_conditions_fails() {
    let registry = setup();

    // Registering with conditions_hash = 0 should fail
    registry.register_covenant(1, 0);
}
