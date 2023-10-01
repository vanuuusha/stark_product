from asyncio import sleep
import random
import re
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.account.account import Account
from starknet_py.net.models import StarknetChainId
from loguru import logger

from starknet_py.net.signer.stark_curve_signer import (
    StarkCurveSigner,
    KeyPair,
)
from helper import calculate_address
from src.modules.swaps.utils.tokens import tokens

from config import (
    MAX_FEE_FOR_TRANSACTION,
    RPC_URL,
)
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.networks import MAINNET
from src.modules.swaps.zk_lend.utils.transaction_data import (
    get_approve_call,
    get_deposit_call,
    get_collateral_call,
    get_withdraw_call, get_withdraw_all_call,
)

from src.utils.transaction_data import (
    get_balance,
    create_amount,
)

class ZKLendLiquidity:
    def __init__(self, private_key: str, token: str, amount_from: float, amount_to: float) -> None:
        self.private_key = private_key
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
        self.token = token
        self.amount = round(random.uniform(amount_from, amount_to), 6)
        self.contract_address = 0x4c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05

    async def add_liquidity(self) -> None:
        token_address = tokens[self.token.upper()]
        amount = await create_amount(18 if self.token.lower() == 'eth' else 6, self.amount)
        balance = await get_balance(token_address, self.account)

        if amount > balance:
            logger.error(f'Not enough {self.token.upper()} balance {hex(self.account.address)}')
            return

        approve_call = await get_approve_call(contract_address=self.contract_address, to_address=token_address,
                                              value=amount)
        deposit_call = await get_deposit_call(contract_address=self.contract_address, value=amount,
                                              from_token_address=token_address)
        collateral_call = await get_collateral_call(contract_address=self.contract_address,
                                                    from_token_address=token_address)
        calls = [approve_call, deposit_call, collateral_call]

        retries = 0
        while retries < 3:
            try:
                self.account.ESTIMATED_FEE_MULTIPLIER = 1
                invoke_tx = await self.account.sign_invoke_transaction(calls=calls, auto_estimate=True)
                estimate_fee = await self.account._estimate_fee(invoke_tx)
                if estimate_fee.overall_fee / 10 ** 18 > MAX_FEE_FOR_TRANSACTION:
                    logger.info('Текущий газ слишком дорогой...')
                    sleep_time = random.randint(45, 75)
                    logger.info(f'Засыпаю на {sleep_time} секунд')
                    await sleep(sleep_time)
                    continue
                tx = await self.account.client.send_transaction(invoke_tx)
                logger.debug(f'Транзакция отправлена. Жду... TX: https://starkscan.co/tx/{hex(tx.transaction_hash)}')
                await sleep(15)
                await self.account.client.wait_for_tx(tx.transaction_hash)
                logger.success(f'Успешно добавлена ликвидность {self.amount} {self.token} | TX: https://starkscan.co/tx/{hex(tx.transaction_hash)}')
                break
            except Exception as ex:
                retries += 1
                logger.error(f'Что-то пошло не так {ex}')
                logger.debug('Пробую еще раз')
                time_sleep = random.randint(70, 90)
                logger.debug(f'Засыпаю на {time_sleep} секунд...')
                await sleep(time_sleep)
                continue


class ZKLendLiquidityRemove:
    def __init__(self, private_key: str, token: str, remove_all: bool, removing_percentage: float) -> None:
        self.private_key = private_key
        private_key = re.sub(r'[^0-9a-fA-F]+', '', private_key)
        private_key = int(private_key, 16)
        address = calculate_address(private_key)
        key_pair = KeyPair.from_private_key(private_key)
        self.account = Account(
            address=address,
            client=FullNodeClient(
                node_url=RPC_URL) if RPC_URL != 'https://alpha-mainnet.starknet.io' else GatewayClient(net=MAINNET),
            signer=StarkCurveSigner(account_address=address, key_pair=key_pair, chain_id=StarknetChainId.MAINNET)
        )
        self.token = token
        self.contract_address = 0x4c0a5193d58f74fbace4b74dcf65481e734ed1714121bdc571da345540efa05
        self.remove_all = remove_all
        self.removing_percentage = removing_percentage

    async def remove_liquidity(self) -> None:
        liquidity_token_address = tokens[self.token]
        balance = await get_balance(liquidity_token_address, self.account)
        if balance == 0:
            logger.error("Похоже что у вас нет ликвидности для удаления")
            return
        if self.remove_all is True:
            withdraw_call = await get_withdraw_all_call(self.contract_address, liquidity_token_address)
        else:
            print(balance)
            amount = int(balance * self.removing_percentage / 100)
            print(amount)
            withdraw_call = await get_withdraw_call(self.contract_address, liquidity_token_address, amount)

        calls = [withdraw_call]

        retries = 0
        while retries < 3:
            try:
                self.account.ESTIMATED_FEE_MULTIPLIER = 1
                invoke_tx = await self.account.sign_invoke_transaction(calls=calls, auto_estimate=True)
                estimate_fee = await self.account._estimate_fee(invoke_tx)
                if estimate_fee.overall_fee / 10 ** 18 > MAX_FEE_FOR_TRANSACTION:
                    logger.info('Текущий газ слишком дорогой...')
                    sleep_time = random.randint(45, 75)
                    logger.info(f'Засыпаю на {sleep_time}')
                    await sleep(sleep_time)
                    continue
                tx = await self.account.client.send_transaction(invoke_tx)
                logger.debug(f'Транзакция отправлена. Жду... TX: https://starkscan.co/tx/{hex(tx.transaction_hash)}')
                await sleep(15)
                await self.account.client.wait_for_tx(tx.transaction_hash)
                logger.success(f'Удаляю {"все" if self.remove_all else f"{self.removing_percentage * 100}%"} токены из пула zklend |  TX: https://starkscan.co/tx/{hex(tx.transaction_hash)}')
                break
            except Exception as ex:
                retries += 1
                if 'assert_not_zero' in str(ex):
                    logger.error("У вас нет токенов для вывода")
                    return
                logger.error(f'Что-то пошло не так {ex}')
                logger.debug('Пробую еще раз')
                time_sleep = random.randint(70, 90)
                logger.debug(f'Засыпаю на {time_sleep} секунд...')
                await sleep(time_sleep)
                continue
