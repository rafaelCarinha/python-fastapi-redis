import asyncio

from async_substrate_interface import AsyncSubstrateInterface
from bittensor.core.chain_data import decode_account_id
from bittensor.core.subtensor import Subtensor

import logging

from bittensor.utils.balance import check_and_convert_to_balance
from bittensor_wallet import Wallet
from bittensor_wallet.utils import SS58_FORMAT
from dotenv import load_dotenv
from typing import Dict, List, Tuple, Optional

import os

# Load environment variables from the .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set log level to INFO (change to DEBUG for more detailed logs)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

OPENTENSOR_URL = os.environ.get("OPENTENSOR_URL")


# Function to fetch Tao dividends
async def fetch_tao_dividends(netuid: int, hotkey: str):
    """
    Fetch Tao dividends for a specific netuid and hotkey asynchronously.
    :param netuid: The specific network ID (subnet) to query.
    :param hotkey: The hotkey to filter results.
    :return: A tuple containing the decoded hotkey, its dividend value, and block hash, or None if no result is found.
    """
    logger.info(f"Starting fetch_tao_dividends for netuid: {netuid}, hotkey: {hotkey}")

    async def collect_results(query_map_result):
        """
        Collect results from the query_map generator.
        :param query_map_result: The result of query_map.
        :return: A list of key-value pairs.
        """
        results = []
        try:
            async for k, v in await query_map_result:
                logger.debug(f"Retrieved raw result - Key: {k}, Value: {v}")
                results.append((k, v))
        except Exception as e:
            logger.error(f"Error occurred while collecting query results: {e}")
            raise
        return results

    try:
        async with AsyncSubstrateInterface(
                url="wss://entrypoint-finney.opentensor.ai:443",
                ss58_format=SS58_FORMAT
        ) as substrate:
            logger.info(f"Connected to Substrate node at wss://entrypoint-finney.opentensor.ai:443")

            # Get the latest block hash
            block_hash = await substrate.get_chain_head()
            logger.debug(f"Fetched latest block hash: {block_hash}")

            # Query the TaoDividendsPerSubnet map for the given netuid
            logger.debug(f"Querying SubtensorModule.TaoDividendsPerSubnet for netuid: {netuid}")
            query_map_result = substrate.query_map(
                "SubtensorModule",
                "TaoDividendsPerSubnet",
                [netuid],
                block_hash=block_hash
            )

            # Collect and decode results
            logger.debug(f"Collecting results from query_map generator...")
            all_results = await collect_results(query_map_result)

            logger.info(f"Collected {len(all_results)} results from query_map for netuid: {netuid}")

            # Filter results based on the provided hotkey
            filtered_results = [
                (decode_account_id(k), v.value) for k, v in all_results if decode_account_id(k) == hotkey
            ]
            logger.debug(f"Filtered results for hotkey '{hotkey}': {filtered_results}")

            # Return the first match or None if not found
            if filtered_results:
                logger.info(f"Found matching dividend for hotkey '{hotkey}': {filtered_results[0]}")
                return filtered_results[0], block_hash
            else:
                logger.warning(f"No matching dividend found for hotkey '{hotkey}'. Returning None.")
                return None, block_hash

    except Exception as e:
        logger.error(f"An error occurred in fetch_tao_dividends: {e}")
        raise


async def fetch_all_netuids() -> Dict[int, List[Tuple[str, int]]]:
    """
    Fetches Tao dividends for all netuids and their associated hotkeys.

    Returns:
        Dict[int, List[Tuple[hotkey (str), dividend (int)]]]:
        Mapping of netuids to their associated accounts (hotkeys) and dividends.
    """
    results = {}

    async with AsyncSubstrateInterface(
            url="wss://entrypoint-finney.opentensor.ai:443",
            ss58_format=42,  # Adjust SS58_FORMAT to match your network settings.
    ) as substrate:
        logger.info("Successfully connected to the Substrate node.")

        # Get latest block hash
        block_hash = await substrate.get_chain_head()
        logger.debug(f"Retrieved block hash: {block_hash}")

        # Query TaoDividendsPerSubnet from the Substrate node at latest block
        query = await substrate.query_map(
            module='SubtensorModule',
            storage_function='TaoDividendsPerSubnet',
            params=[],
            block_hash=block_hash
        )

        async for raw_key, raw_value in query:
            # Robustly decode the raw key into bytes
            key_bytes = decode_raw_key(raw_key)
            if key_bytes is None:
                logger.warning(f"Skipping unsupported key structure: {raw_key}")
                continue

            # Decode account id from bytes
            try:
                account_id = substrate.ss58_encode(key_bytes)
                logger.debug(f"Decoded account ID: {account_id}")
            except Exception as e:
                logger.error(f"Failed to convert key bytes to account ID: {e}. Raw key: {raw_key}")
                continue

            # Safely extract netuid and dividend values from the raw value
            netuid, dividend = extract_netuid_and_dividend(raw_value)
            if netuid is None or dividend <= 0:
                logger.warning(f"Invalid or zero dividend data received: {raw_value}")
                continue

            # Add data to the results dictionary
            results.setdefault(netuid, []).append((account_id, dividend))
            logger.debug(f"Recorded netuid: {netuid}, account: {account_id}, dividend: {dividend}")

    logger.info(f"Completed fetching Tao dividends. Netuids processed: {len(results)}")
    return results


def decode_raw_key(raw_key) -> Optional[bytes]:
    """
    Decodes a nested tuple raw key into bytes. Handles the nested structures.

    Args:
        raw_key: The raw key obtained from substrate storage maps.

    Returns:
        Bytes representation of the innermost tuple if valid, otherwise None.
    """
    try:
        if isinstance(raw_key, (bytes, bytearray)):
            return raw_key

        if isinstance(raw_key, tuple) and len(raw_key) > 1 and isinstance(raw_key[1], tuple):
            inner_nested = raw_key[1]

            # Handle nested tuple ((int, int, ...),)
            if len(inner_nested) == 1 and isinstance(inner_nested[0], tuple):
                innermost = inner_nested[0]

                if all(isinstance(i, int) and 0 <= i <= 255 for i in innermost):
                    return bytes(innermost)

    except Exception as e:
        logger.error(f"Exception decoding raw key {raw_key}: {e}")

    logger.warning(f"Unrecognized key structure: {raw_key}")
    return None


def extract_netuid_and_dividend(value) -> Tuple[Optional[int], int]:
    """
    Safely extracts netuid and dividend from raw substrate storage entry values.

    Args:
        value: The value object from substrate query.

    Returns:
        Tuple (netuid, dividend). Returns (None, 0) if extraction fails.
    """
    try:
        netuid = getattr(value, "key", None)
        dividend = getattr(value, "value", 0)

        return netuid, dividend
    except Exception as e:
        logger.error(f"Failed to extract netuid and dividend from value {value}: {e}")
        return None, 0


async def fetch_all_hotkeys_for_netuid(netuid: int):
    """
    Fetch tao dividends for all hotkeys under a specific netuid.
    :param netuid: The ID of the network to query.
    :return: A list of hotkey-dividend tuples for the given netuid.
    """
    results = []
    async with AsyncSubstrateInterface(
            url="wss://entrypoint-finney.opentensor.ai:443",
            ss58_format=SS58_FORMAT,
    ) as substrate:
        # Get the latest block hash
        block_hash = await substrate.get_chain_head()

        # Query TaoDividendsPerSubnet for a single netuid
        query_map_result = substrate.query_map(
            "SubtensorModule",
            "TaoDividendsPerSubnet",
            [netuid],
            block_hash=block_hash
        )

        # Collect results
        async for k, v in await query_map_result:
            decoded_key = decode_account_id(k)
            results.append((decoded_key, v.value))

    return results


# Function to stake Tao
def stake_tao(hotkey: str, netuid: int, amount: float):
    """Async function to stake Tao for a specific hotkey and netuid."""
    logger.info(f"Staking Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}")
    try:
        # Validate and convert the amount to balance
        amount = check_and_convert_to_balance(amount)

        wallet = Wallet(name="default", path="~/.bittensor/wallets")
        wallet.create_new_coldkey(overwrite=True, use_password=False)

        print(f"Coldkey for wallet '{wallet.name}' has been regenerated.")

        # Initialize Subtensor with the correct WebSocket endpoint
        subtensor = Subtensor(network="wss://entrypoint-finney.opentensor.ai:443")
        # Perform the async staking operation
        result = subtensor.add_stake(
            wallet=wallet,
            netuid=netuid,
            hotkey_ss58=hotkey,
            amount=amount,
            wait_for_inclusion=True,
            wait_for_finalization=False,
            safe_staking=False,
            allow_partial_stake=False,
        )
        logger.info(f"Successfully staked Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}")
        return result
    except Exception as e:
        logger.error(f"Error staking Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}. Error: {e}")
        raise


# Function to unstake Tao
def unstake_tao(hotkey: str, netuid: int, amount: float):
    """Async function to unstake Tao for a specific hotkey and netuid."""
    logger.info(f"Unstaking Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}")
    try:
        # Validate and convert the amount to balance
        amount = check_and_convert_to_balance(amount)

        wallet = Wallet(name="default", path="~/.bittensor/wallets")
        wallet.create_new_coldkey(overwrite=True, use_password=False)

        print(f"Coldkey for wallet '{wallet.name}' has been regenerated.")

        # Initialize Subtensor with the correct WebSocket endpoint
        subtensor = Subtensor(network="wss://entrypoint-finney.opentensor.ai:443")
        # Perform the async unstaking operation
        result = subtensor.unstake(
            wallet=wallet,
            netuid=netuid,
            hotkey_ss58=hotkey,
            amount=amount,
            wait_for_inclusion=True,
            wait_for_finalization=False,
            safe_staking=False,
            allow_partial_stake=False,
        )
        logger.info(f"Successfully unstaked Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}")
        return result
    except Exception as e:
        logger.error(f"Error unstaking Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}. Error: {e}")
        raise
