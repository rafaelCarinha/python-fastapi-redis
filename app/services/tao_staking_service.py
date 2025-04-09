import asyncio
from bittensor.core.subtensor import Subtensor

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set log level to INFO (change to DEBUG for more detailed logs)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Function to fetch Tao dividends
async def fetch_tao_dividends(netuid: int, hotkey: str):
    logger.info(f"Fetching Tao dividends for hotkey: {hotkey} on netuid: {netuid}")
    try:
        subtensor = Subtensor(network="nakamoto")
        result = await subtensor.async_tao_dividends_for_hotkey(netuid=netuid, hotkey=hotkey)
        logger.info(f"Successfully fetched Tao dividends for hotkey: {hotkey} on netuid: {netuid}")
        return result
    except Exception as e:
        logger.error(f"Error fetching Tao dividends for hotkey: {hotkey} on netuid: {netuid}. Error: {e}")
        raise


# Function to stake Tao
async def stake_tao(hotkey: str, netuid: int, amount: float):
    logger.info(f"Staking Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}")
    try:
        subtensor = Subtensor(network="nakamoto")
        result = await subtensor.async_stake_hotkey_on_subnet(netuid=netuid, hotkey=hotkey, amount=amount)
        logger.info(f"Successfully staked Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}")
        return result
    except Exception as e:
        logger.error(f"Error staking Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}. Error: {e}")
        raise


# Function to unstake Tao
async def unstake_tao(hotkey: str, netuid: int, amount: float):
    logger.info(f"Unstaking Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}")
    try:
        subtensor = Subtensor(network="nakamoto")
        result = await subtensor.async_unstake_hotkey_on_subnet(netuid=netuid, hotkey=hotkey, amount=amount)
        logger.info(f"Successfully unstaked Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}")
        return result
    except Exception as e:
        logger.error(f"Error unstaking Tao: {amount} for hotkey: {hotkey} on netuid: {netuid}. Error: {e}")
        raise
