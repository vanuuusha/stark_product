from asyncio import sleep
import random
import re
from starknet_py.net.networks import MAINNET
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.address import compute_address
from starknet_py.net.account.account import Account
from starknet_py.net.models import StarknetChainId
from starknet_py.cairo import felt
from loguru import logger
import sys

from config import (
    MAX_FEE_FOR_TRANSACTION,
    RPC_URL,
)
from helper import calculate_address

from starknet_py.net.signer.stark_curve_signer import (
    KeyPair,
    StarkCurveSigner,
)

from src.utils.transaction_data import (
    get_balance,
    setup_token_addresses,
)


class BaseLiquidityRemove:
    def __init__(self, private_key: str, from_token_pair: str, remove_all: bool, removing_percentage: float) -> None:
        private_key = re.sub(r'[^0-9a-fA-F]+', '', private_key)
        private_key = int(private_key, 16)
        key_pair = KeyPair.from_private_key(private_key)
        address = calculate_address(private_key)
        self.account = Account(
            address=address,
            client=FullNodeClient(
                node_url=RPC_URL) if RPC_URL != 'https://alpha-mainnet.starknet.io' else GatewayClient(net=MAINNET),
            signer=StarkCurveSigner(account_address=address, key_pair=key_pair, chain_id=StarknetChainId.MAINNET)
        )
        self.from_token_pair = from_token_pair
        self.remove_all = remove_all
        self.removing_percentage = removing_percentage

    async def remove_liquidity(self) -> None:
        contract_address = await self.get_contract_address()
        liquidity_token = await self.get_liquidity_token()
        liquidity_balance = await get_balance(liquidity_token, self.account)
        from_token_address, to_token_address = await setup_token_addresses('ETH', self.from_token_pair)

        if liquidity_balance == 0:
            logger.error(f"Looks like you don't have any liquidity to remove {hex(self.account.address)}")
            return

        if self.remove_all is True:
            amount = liquidity_balance
        else:
            amount = int(liquidity_balance * self.removing_percentage)

        calls = await self.get_calls(contract_address, from_token_address, to_token_address, liquidity_token,
                                     amount, self.account)
        retries = 0
        while retries < 3:
            try:
                self.account.ESTIMATED_FEE_MULTIPLIER = 1
                invoke_tx = await self.account.sign_invoke_transaction(calls=calls, auto_estimate=True)
                estimate_fee = await self.account._estimate_fee(invoke_tx)
                if estimate_fee.overall_fee / 10 ** 18 > MAX_FEE_FOR_TRANSACTION:
                    logger.info('Текущий газ слишком большой...')
                    sleep_time = random.randint(45, 75)
                    logger.info(f'Засыпаю на {sleep_time} секунд')
                    await sleep(sleep_time)
                    continue
                tx = await self.account.client.send_transaction(invoke_tx)
                logger.debug(f'Транзакция отправлена, ожидаю... TX: https://starkscan.co/tx/{hex(tx.transaction_hash)}')
                await sleep(15)
                await self.account.client.wait_for_tx(tx.transaction_hash)
                logger.success(
                    f'Removed {"all" if self.remove_all else f"{self.removing_percentage * 100}%"} tokens from {await self.get_pool_name()} pool |  TX: https://starkscan.co/tx/{hex(tx.transaction_hash)}')
                break
            except Exception as ex:
                retries += 1
                logger.error(f'Что-то пошло не так {ex}')
                logger.debug('Повторяю')
                time_sleep = random.randint(40, 60)
                logger.debug(f'Засыпаю на {time_sleep} секунд...')
                await sleep(time_sleep)
                continue

    async def get_contract_address(self) -> None:
        raise NotImplementedError("Subclasses must implement get_contract_address()")

    async def get_liquidity_token(self) -> None:
        raise NotImplementedError("Subclasses must implement get_liquidity_token()")

    async def get_calls(self, contract_address: felt, from_token_address: felt, to_token_address: felt,
                        liquidity_token: felt, amount: int, account: Account
                        ) -> None:
        raise NotImplementedError("Subclasses must implement get_calls()")

    async def get_pool_name(self) -> None:
        raise NotImplementedError("Subclasses must implement get_pool_name()")
