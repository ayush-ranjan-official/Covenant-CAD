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

    print(f"Registering vault {vault_id} with conditions 0x{conditions_hash:X}...")
    invocation = await contract.functions["register_covenant"].invoke_v3(
        vault_id, conditions_hash,
        resource_bounds=RESOURCE_BOUNDS
    )
    await invocation.wait_for_acceptance()
    print(f"Vault registered! TX: {hex(invocation.hash)}")
    print(f"View: https://sepolia.voyager.online/tx/{hex(invocation.hash)}")

asyncio.run(main())
