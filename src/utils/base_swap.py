from asyncio import sleep
import random
import re

from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.net.account.account import Account
from starknet_py.cairo import felt
from loguru import logger
from starknet_py.net.networks import MAINNET

from starknet_py.net.signer.stark_curve_signer import (
    StarkCurveSigner,
    KeyPair,
)

from config import (
    MAX_FEE_FOR_TRANSACTION,
    RPC_URL,
)

from src.utils.transaction_data import (
    setup_token_addresses,
    create_amount,
    get_balance,
)
from helper import calculate_address


class BaseSwap:
    def __init__(self,
                 private_key: str,
                 from_token: str,
                 to_token: str,
                 amount_from: float,
                 amount_to: float,
                 swap_all_balance: bool,
                 ) -> None:
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
        self.from_token = from_token
        self.to_token = to_token
        self.amount = round(random.uniform(amount_from, amount_to), 6)
        self.swap_all_balance = swap_all_balance


    async def swap(self) -> None:
        contract_address = await self.get_contract_address()
        from_token_address, to_token_address = await setup_token_addresses(self.from_token, self.to_token)
        amount = await create_amount(18 if self.from_token.lower() == 'eth' else 6, self.amount)
        balance = await get_balance(from_token_address, self.account)
        if self.swap_all_balance is True and self.from_token.lower() == 'eth':
            logger.error("You can't use swap_all_balance = True with ETH. Using amount_from, amount_to.")
        if self.swap_all_balance is True and self.from_token.lower() != 'eth':
            amount = balance
        if amount > balance:
            logger.error(f'Not enough balance {hex(self.account.address)}')
            return

        approve_call = await self.get_approve_call(from_token_address, contract_address, amount)
        swap_call = await self.get_swap_call(contract_address, self.account, from_token_address, to_token_address, amount)

        calls = [approve_call, swap_call]
        retries = 0
        while retries < 3:
            try:
                self.account.ESTIMATED_FEE_MULTIPLIER = 1
                invoke_tx = await self.account.sign_invoke_transaction(calls=calls, auto_estimate=True)
                estimate_fee = await self.account._estimate_fee(invoke_tx)
                if estimate_fee.overall_fee / 10 ** 18 > MAX_FEE_FOR_TRANSACTION:
                    logger.info('Текущий газ слишком высок, засыпаю...')
                    sleep_time = random.randint(45, 75)
                    logger.info(f'Засыпаю на {sleep_time} секунд')
                    await sleep(sleep_time)
                    continue
                tx = await self.account.client.send_transaction(invoke_tx)
                logger.debug(f'Транзация отправлена. Жду... TX: https://starkscan.co/tx/{hex(tx.transaction_hash)}')
                await sleep(15)
                await self.account.client.wait_for_tx(tx.transaction_hash)
                logger.success(f'Успешный обмем {"all" if self.swap_all_balance is True and self.from_token.lower() != "eth" else self.amount} {self.from_token} => {self.to_token} TX: https://starkscan.co/tx/{hex(tx.transaction_hash)}')
                break
            except Exception as ex:
                retries += 1
                logger.error(f'Что-то пошло не так {ex}')
                logger.debug('Пробую ещё раз')
                time_sleep = random.randint(40, 60)
                logger.debug(f'Засыпаю на {time_sleep} секунд...')
                await sleep(time_sleep)
                continue

    async def get_approve_call(self, from_token_address: felt, contract_address: felt, amount: int) -> None:
        raise NotImplementedError("Subclasses must implement get_approve_call()")

    async def get_swap_call(self, contract_address: felt, account: Account, from_token_address: felt,
                            to_token_address: felt, amount: int) -> None:
        raise NotImplementedError("Subclasses must implement get_swap_call()")

    async def get_contract_address(self) -> None:
        raise NotImplementedError("Subclasses must implement get_contract_address()")
