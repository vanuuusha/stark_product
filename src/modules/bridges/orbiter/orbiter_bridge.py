from fractions import Fraction
from asyncio import sleep
import random
import re
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.hash.address import compute_address
from starknet_py.net.account.account import Account
from starknet_py.net.models import StarknetChainId
from loguru import logger

from starknet_py.net.signer.stark_curve_signer import (
    KeyPair,
    StarkCurveSigner
)
from config import (
    MAX_FEE_FOR_TRANSACTION,
    RPC_URL,
)

from src.utils.transaction_data import (
    get_balance,
)
from starknet_py.net.gateway_client import GatewayClient
from src.modules.bridges.orbiter.utils.transaction_data import (
    get_approve_call,
    get_transfer_call,
)
from starknet_py.net.networks import MAINNET
from helper import calculate_address

class OrbiterBridgeWithdraw:
    def __init__(self,
                 private_key: str,
                 chain: str,
                 receiver_address: str,
                 amount_from: float,
                 amount_to: float,
                 bridge_all_balance: bool,
                 code: int
                 ) -> None:
        private_key = re.sub(r'[^0-9a-fA-F]+', '', private_key)
        private_key = int(private_key, 16)
        self.receiver_address = re.sub(r'[^0-9a-fA-F]+', '', receiver_address)
        self.receiver_address = int(receiver_address, 16)
        key_pair = KeyPair.from_private_key(private_key)
        address = calculate_address(private_key)

        self.account = Account(
            address=address,
            client=FullNodeClient(
                node_url=RPC_URL) if RPC_URL != 'https://alpha-mainnet.starknet.io' else GatewayClient(net=MAINNET),
            signer=StarkCurveSigner(account_address=address, key_pair=key_pair, chain_id=StarknetChainId.MAINNET)
        )
        self.chain = chain
        self.amount = round(random.uniform(amount_from, amount_to), 6)
        self.bridge_all_balance = bridge_all_balance
        self.code = code

    async def withdraw(self) -> None:
        balance = await get_balance(0x049D36570D4e46f48e99674bd3fcc84644DdD6b96F7C741B1562B82f9e004dC7, self.account)
        if self.bridge_all_balance is True:
            amount = balance // 10 ** 13 * 10 ** 13
        else:
            amount = int(self.amount * 10 ** 18)

        if amount > balance:
            logger.error(f'Not enough balance for wallet {hex(self.account.address)}')

        amount = int(str(Fraction(amount))[:-4] + str(self.code))

        approve_call = await get_approve_call(0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7,
                                              amount)
        transfer_call = await get_transfer_call(amount, self.receiver_address)
        calls = [approve_call, transfer_call]
        retries = 0

        while retries < 3:
            try:
                self.account.ESTIMATED_FEE_MULTIPLIER = 1
                invoke_tx = await self.account.sign_invoke_transaction(calls=calls, auto_estimate=True)
                estimate_fee = await self.account._estimate_fee(invoke_tx)
                if estimate_fee.overall_fee / 10 ** 18 > MAX_FEE_FOR_TRANSACTION:
                    logger.info('Текущие цены на газ слишком велики...')
                    sleep_time = random.randint(45, 75)
                    logger.info(f'Засыпаю на {sleep_time} секунд')
                    await sleep(sleep_time)
                    continue
                tx = await self.account.client.send_transaction(invoke_tx)
                logger.debug(f'Транзакция отправлена. Ошидаю... TX: https://starkscan.co/tx/{hex(tx.transaction_hash)}')
                await sleep(15)
                await self.account.client.wait_for_tx(tx.transaction_hash)
                logger.success(
                    f'Успешный бридж {"all" if self.bridge_all_balance is True else self.amount} ETH tokens => {self.chain} TX: https://starkscan.co/tx/{hex(tx.transaction_hash)}'
                )
                break
            except Exception as ex:
                retries += 1
                logger.error(f'Что-то пошло не так {ex}')
                logger.debug('Пробую еще раз')
                time_sleep = random.randint(40, 60)
                logger.debug(f'Засыпаю на {time_sleep} секунд...')
                await sleep(time_sleep)
                continue


