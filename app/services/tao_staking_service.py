import asyncio
from bittensor.core.subtensor import Subtensor


async def fetch_tao_dividends(netuid: int, hotkey: str):
    subtensor = Subtensor(network="nakamoto")
    return await subtensor.async_tao_dividends_for_hotkey(netuid=netuid, hotkey=hotkey)


async def stake_tao(hotkey: str, netuid: int, amount: float):
    subtensor = Subtensor(network="nakamoto")
    return await subtensor.async_stake_hotkey_on_subnet(netuid=netuid, hotkey=hotkey, amount=amount)


async def unstake_tao(hotkey: str, netuid: int, amount: float):
    subtensor = Subtensor(network="nakamoto")
    return await subtensor.async_unstake_hotkey_on_subnet(netuid=netuid, hotkey=hotkey, amount=amount)