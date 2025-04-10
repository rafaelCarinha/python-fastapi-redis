import asyncio

from async_substrate_interface import AsyncSubstrateInterface
from bittensor.core.chain_data import decode_account_id
from bittensor.core.subtensor import Subtensor

import logging

from bittensor.utils.balance import check_and_convert_to_balance
from bittensor_wallet import Wallet
from bittensor_wallet.utils import SS58_FORMAT
from dotenv import load_dotenv

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
    :return: A tuple containing the decoded hotkey, its dividend value, and block hash.
    """

    async def collect_results(query_map_result):
        """
        Collect results from the query_map generator.
        :param query_map_result: The result of query_map.
        :return: A list of key-value pairs.
        """
        results = []
        async for k, v in await query_map_result:
            results.append((k, v))
        return results

    async with AsyncSubstrateInterface(
            url="wss://entrypoint-finney.opentensor.ai:443",
            ss58_format=SS58_FORMAT
    ) as substrate:
        # Get the latest block hash
        block_hash = await substrate.get_chain_head()

        # Query the TaoDividendsPerSubnet map for the given netuid
        query_map_result = substrate.query_map(
            "SubtensorModule",
            "TaoDividendsPerSubnet",
            [netuid],
            block_hash=block_hash
        )

        # Collect and decode results
        all_results = await collect_results(query_map_result)
        filtered_results = [
            (decode_account_id(k), v.value) for k, v in all_results if decode_account_id(k) == hotkey
        ]

        # Return the first match or None if not found
        if filtered_results:
            return filtered_results[0], block_hash
        else:
            return None, block_hash


##TODO - Debug and fix the returned data:  Invalid data in value object: BittensorScaleType
async def fetch_all_netuids():
    """
    Fetch tao dividends for all netuids and their associated hotkeys.
    :return: A dictionary with netuids as keys and lists of hotkey-dividend pairs as values.
    """
    results = {}
    async with AsyncSubstrateInterface(
            url="wss://entrypoint-finney.opentensor.ai:443",
            ss58_format=SS58_FORMAT,
    ) as substrate:
        # Get the latest block hash
        block_hash = await substrate.get_chain_head()

        # Query TaoDividendsPerSubnet for all netuids (empty array indicates all)
        query_map_result = substrate.query_map(
            "SubtensorModule",
            "TaoDividendsPerSubnet",
            [],
            block_hash=block_hash
        )

        # Collect results
        async for k, v in await query_map_result:
            # Log the raw received data
            logger.info("Raw data received -> Key: %s (Type: %s), Value: %s (Type: %s)",
                        k, type(k), v, type(v))

            # Check and process the key (k)
            if isinstance(k, tuple):  # Handle tuple case
                if len(k) > 0:
                    logger.debug("Key is a tuple, extracting the first element.")
                    k = k[0]
                else:
                    logger.warning("Received an empty tuple for key, skipping.")
                    continue

            logger.debug("Processed key after tuple handling: %s, Type: %s", k, type(k))

            if isinstance(k, int):  # If the key is an integer, convert it to bytes
                logger.debug("Key is an integer (%d), attempting conversion to bytes.", k)
                k = str(k).encode()  # Convert the integer to byte-representable form
                logger.debug("Converted integer key to bytes: %s", k)

            # Check if the key is now bytes-like
            if isinstance(k, (bytes, bytearray)):
                try:
                    decoded_key = decode_account_id(k)  # Decode the account ID

                    # Attempt to extract `key` and `value` from `v`
                    netuid = getattr(v, "key", None)
                    dividend_value = getattr(v, "value", None)

                    # Validate `netuid` and `dividend_value`
                    if netuid is None or dividend_value is None:
                        logger.warning("Invalid data in value object: %s, skipping.", v)
                        continue

                    # Add to results dictionary
                    if netuid not in results:
                        results[netuid] = []
                    results[netuid].append((decoded_key, dividend_value))

                    logger.debug("Decoded key: %s, NetUID: %s, Dividend: %s",
                                 decoded_key, netuid, dividend_value)
                except Exception as e:
                    logger.error("Failed to decode key: %s, Error: %s", k, str(e))
            else:
                logger.warning("Key is not a bytes-like object after processing: %s, skipping.", k)

    return results

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

        # Initialize the wallet using the provided hotkey
        wallet = Wallet(name="default", path="~/.bittensor/wallets")

        # Initialize Subtensor with the correct WebSocket endpoint
        subtensor = Subtensor(network="wss://entrypoint-finney.opentensor.ai:443")
        # Perform the async staking operation
        result = subtensor.add_stake(
            wallet= wallet,
            netuid=netuid,
            hotkey_ss58=hotkey,
            amount=amount,
            wait_for_inclusion= True,
            wait_for_finalization= False,
            safe_staking= False,
            allow_partial_stake = False,
            rate_tolerance= 0.005,
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

        # Initialize the wallet using the provided hotkey
        wallet = Wallet(name="default", path="~/.bittensor/wallets")

        # Initialize Subtensor with the correct WebSocket endpoint
        subtensor = Subtensor(network="wss://entrypoint-finney.opentensor.ai:443")
        # Perform the async unstaking operation
        result = subtensor.unstake(
            wallet= wallet,
            netuid=netuid,
            hotkey_ss58=hotkey,
            amount=amount,
            wait_for_inclusion= True,
            wait_for_finalization= False,
            safe_staking= False,
            allow_partial_stake = False,
            rate_tolerance= 0.005,
        )
        logger.info(f"Successfully unstaked Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}")
        return result
    except Exception as e:
        logger.error(f"Error unstaking Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}. Error: {e}")
        raise
