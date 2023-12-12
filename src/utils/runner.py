import random
from loguru import logger
from src.modules.swaps.anvuswap.anvuswap import AnvuSwap
from asyncio import sleep
from config import *
from okx import okx_withdrawal_subs
import re
from src.modules.swaps.fibrous_swap.fibrous_swap import FibrousSwap
import string
from src.modules.bridges.orbiter.orbiter_bridge import (
    OrbiterBridgeWithdraw,
)
from starknet_py.hash.selector import get_selector_from_name
from starknet_py.net.client_models import Call
from src.modules.swaps.k10_swap.k10_swap import (
    K10LiquidityRemove,
    K10Liquidity,
    K10Swap,
)

from src.modules.swaps.sithswap.sithswap import (
    SithLiquidityRemove,
    SithSwapLiquidity,
    SithSwap,
)

from src.modules.swaps.myswap.myswap import (
    MySwapLiquidityRemove,
    MySwapLiquidity,
    MySwap,
)

from src.modules.swaps.zk_lend.zk_lend import (
    ZKLendLiquidity,
    ZKLendLiquidityRemove,
)

from src.utils.chains import (
    chain_mapping,
)

from starknet_py.net.account.account import Account
from starknet_py.net.full_node_client import FullNodeClient
from starknet_py.net.models.chains import StarknetChainId
from starknet_py.net.networks import MAINNET
from starknet_py.net.gateway_client import GatewayClient
from starknet_py.net.signer.stark_curve_signer import (
    StarkCurveSigner,
    KeyPair,
)

from src.modules.swaps.jediswap.jediswap import (
    JediLiquidityRemove,
    JediLiquidity,
    JediSwap,
)
from starknet_py.hash.selector import get_selector_from_name
from web3.auto import w3
from web3 import Web3
from eth_account.signers.local import LocalAccount
from src.utils.transaction_data import (
    setup_token_addresses,
    get_balance,
)
from starknet_py.contract import Contract
from src.utils.minter_abi import MINT_ID_ABI
from src.utils.dmail_abi import DMAIL_TRANSACTION_ABI
from helper import calculate_address

def get_account(private_key):
    private_key = re.sub(r'[^0-9a-fA-F]+', '', private_key)
    private_key = int(private_key, 16)
    key_pair = KeyPair.from_private_key(private_key)
    address = calculate_address(private_key)
    account = Account(
        address=address,
        client=FullNodeClient(
            node_url=RPC_URL) if RPC_URL != 'https://alpha-mainnet.starknet.io' else GatewayClient(net=MAINNET),
        signer=StarkCurveSigner(account_address=address, key_pair=key_pair, chain_id=StarknetChainId.MAINNET)
    )
    return account

def transfer_all_arbitrum_eth(to_address, metamask_key, sender_address):
    import time
    from eth_account import Account
    Account.enable_unaudited_hdwallet_features()
    provider_url = "https://rpc.ankr.com/arbitrum"
    while True:
        try:
            web3 = Web3(Web3.HTTPProvider(provider_url))
            account: LocalAccount = web3.eth.account.from_key(metamask_key)
            private_key = account._private_key
            balance_in_wei = web3.eth.get_balance(sender_address)
        except Exception:
            print('Ошибка в получения данных из блокчейна, повторяю')
            time.sleep(10)
        else:
            break
    balance_in_wei -= web3.to_wei('0.1', 'gwei') * 800000
    if balance_in_wei <= 0:
        return False
    transaction = {
        'to': web3.to_checksum_address(to_address),
        'value': balance_in_wei,
        'gas': 800000,
        'gasPrice': web3.to_wei('0.1', 'gwei'),  # Замените на желаемую цену газа
        'nonce': web3.eth.get_transaction_count(sender_address),
    }
    while True:
        try:
            signed_transaction = web3.eth.account.sign_transaction(transaction, private_key)
            transaction_hash = web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        except Exception:
            print('Ошибка в получения данных из блокчейна, повторяю')
            time.sleep(10)
        else:
            break
    return web3.to_hex(transaction_hash)


async def process_orbiter_bridging(data, count, number) -> None:
    private_keys = data['private_keys']
    private_key_num = data['private_key_num']
    metamask_keys = data['metamask_keys']
    withdraw_address = data['withdraw_address']

    from_token_address, to_token_address = await setup_token_addresses('ETH', 'ETH')
    balance = await get_balance(from_token_address, get_account(private_keys[private_key_num]))
    balance = balance * okx_return_percentage / 10 ** 20

    amount_from = balance - 5 * balance / 100
    amount_to = balance
    code = chain_mapping['ARB'.lower()].code
    chain = 'ARB'

    account = w3.eth.account.from_key(metamask_keys[private_key_num])
    metmask_address = w3.to_checksum_address(account.address)
    bridger = OrbiterBridgeWithdraw(
        private_key=private_keys[private_key_num],
        chain=chain,
        receiver_address=metmask_address,
        amount_from=amount_from,
        amount_to=amount_to,
        bridge_all_balance=False,
        code=code,
    )
    logger.info(f'Аккаунт {number}: Бриджу средства с пощью орбитера в {chain.upper()}...')
    await bridger.withdraw()
    await sleep(100)
    tx_hash = transfer_all_arbitrum_eth(withdraw_address[private_key_num], metamask_keys[private_key_num], metmask_address)
    logger.info(f'Аккаунт {number}: Транзакция в ARB-OKX отправлена https://arbiscan.io/tx/{tx_hash}')
    await sleep(200)
    okx_withdrawal_subs()
    await sleep(10)


async def process_okx_withdraw_stark(data, _, number):
    private_keys = data['private_keys']
    private_key_num = data['private_key_num']
    stark_okx = data['okx_withdraw_stark'][private_key_num]
    stark_okx = re.sub(r'[^0-9a-fA-F]+', '', stark_okx)
    stark_okx = int(stark_okx, 16)
    private_key = private_keys[private_key_num]

    from_token_address, to_token_address = await setup_token_addresses('ETH', 'ETH')
    balance = await get_balance(from_token_address, get_account(private_key))
    balance = int(balance * okx_return_percentage / 100)
    account = get_account(private_key)
    eth_token = 0x049d36570d4e46f48e99674bd3fcc84644ddd6b96f7c741b1562b82f9e004dc7
    call = Call(
        to_addr=eth_token,
        selector=get_selector_from_name('transfer'),
        calldata=[stark_okx, balance, 0],
    )
    tx = await account.execute(calls=[call], cairo_version=1, auto_estimate=True)
    logger.info(f'Аккаунт {number}: Транзакция в OKX отправлена https://starkscan.co/tx/{hex(tx.transaction_hash)}')
    await account.client.wait_for_tx(tx.transaction_hash)
    await sleep(200)
    okx_withdrawal_subs()
    await sleep(10)

async def process_jediswap_swap(private_key: str, count_swaps, number) -> None:
    while count_swaps >= 2:
        from_token = 'ETH'
        to_token = random.choice(jediswap_swap_with_tokens)
        amount_from = jediswap_amount_eth[0]
        amount_to = jediswap_amount_eth[1]
        jediswap_swap = JediSwap(private_key=private_key,
                                 from_token=from_token,
                                 to_token=to_token,
                                 amount_from=amount_from,
                                 amount_to=amount_to,
                                 swap_all_balance=False)
        logger.info(f'Аккаунт {number}: Свапаю на Jediswap {from_token} to {to_token}...')
        await jediswap_swap.swap()
        await sleep(40)
        from_token = to_token
        to_token = 'ETH'
        jediswap_swap = JediSwap(private_key=private_key,
                                 from_token=from_token,
                                 to_token=to_token,
                                 amount_from=amount_from,
                                 amount_to=amount_to,
                                 swap_all_balance=True)
        logger.info(f'Аккаунт {number}: Свапаю на Jediswap {from_token} to {to_token}...')
        await jediswap_swap.swap()
        await sleep(40)
        count_swaps -= 2


async def process_myswap_swap(private_key: str, count_swaps, number) -> None:
    while count_swaps >= 2:
        from_token = 'ETH'
        to_token = random.choice(myswap_swap_with_tokens)
        amount_from = myswap_amount_eth[0]
        amount_to = myswap_amount_eth[1]

        myswap_swap = MySwap(private_key=private_key,
                         from_token=from_token,
                         to_token=to_token,
                         amount_from=amount_from,
                         amount_to=amount_to,
                         swap_all_balance=False)
        logger.info(f'Аккаунт {number}: Свапаю на MySwap {from_token} to {to_token}...')
        await myswap_swap.swap()
        await sleep(40)
        from_token = to_token
        to_token = 'ETH'
        myswap_swap = MySwap(private_key=private_key,
                                 from_token=from_token,
                                 to_token=to_token,
                                 amount_from=amount_from,
                                 amount_to=amount_to,
                                 swap_all_balance=True)
        logger.info(f'Аккаунт {number}: Свапаю на MySwap {from_token} to {to_token}...')
        await myswap_swap.swap()
        await sleep(40)
        count_swaps -= 2


async def process_k10_swap(private_key: str, count_swaps, number) -> None:
    while count_swaps >= 2:
        from_token = 'ETH'
        to_token = random.choice(k10_swap_with_tokens)
        amount_from = k10_amount_eth[0]
        amount_to = k10_amount_eth[1]

        k10_swap = K10Swap(private_key=private_key,
                           from_token=from_token,
                           to_token=to_token,
                           amount_from=amount_from,
                           amount_to=amount_to,
                           swap_all_balance=False)
        logger.info(f'Аккаунт {number}: Свапаю на 10kSwap {from_token} to {to_token}...')
        await k10_swap.swap()
        await sleep(40)
        from_token = to_token
        to_token = 'ETH'
        k10_swap = K10Swap(private_key=private_key,
                             from_token=from_token,
                             to_token=to_token,
                             amount_from=amount_from,
                             amount_to=amount_to,
                             swap_all_balance=True)
        logger.info(f' Аккаунт {number}:Свапаю на 10kSwap {from_token} to {to_token}...')
        await k10_swap.swap()
        await sleep(40)
        count_swaps -= 2


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


async def process_dmail(private_key, count_swaps, number):
    while count_swaps >= 1:
        logger.info(f'Аккаунт {number}: начинаю транзакцию на dmail')
        contract = Contract(
            address=0x0454F0BD015E730E5ADBB4F080B075FDBF55654FF41EE336203AA2E1AC4D4309,
            abi=DMAIL_TRANSACTION_ABI,
            provider=get_account(private_key),
        )

        logger.info(f"Аккаунт {number}: Генерирую сообщения...")
        random_email = f"{get_random_string(6)}".encode()
        random_message = get_random_string(3).encode()

        logger.info(f"Аккаунт {number}: Отправляю транзакцию...")
        invocation = await contract.functions["transaction"].invoke(random_email.hex(), random_message.hex(), auto_estimate=True)

        logger.info(f"Аккаунт {number} {calculate_address(private_key)}: Транзакция ждут подтверждения...")
        await invocation.wait_for_acceptance()
        await sleep(45)
        count_swaps -= 1


async def process_sith_swap(private_key: str, count_swaps, number) -> None:
    while count_swaps >= 2:
        from_token = 'ETH'
        to_token = random.choice(sith_swap_with_tokens)
        amount_from = sith_amount_eth[0]
        amount_to = sith_amount_eth[1]
        sith_swap = SithSwap(private_key=private_key,
                             from_token=from_token,
                             to_token=to_token,
                             amount_from=amount_from,
                             amount_to=amount_to,
                             swap_all_balance=False)
        logger.info(f'Аккаунт {number}: Свапаю на SithSwap {from_token} to {to_token}...')
        await sith_swap.swap()
        await sleep(40)
        from_token = to_token
        to_token = 'ETH'
        sith_swap = SithSwap(private_key=private_key,
                           from_token=from_token,
                           to_token=to_token,
                           amount_from=amount_from,
                           amount_to=amount_to,
                           swap_all_balance=True)
        logger.info(f'Аккаунт {number}: Свапаю на SithSwap {from_token} to {to_token}...')
        await sith_swap.swap()
        await sleep(40)
        count_swaps -= 2


async def process_anvu_swap(private_key: str) -> None:
    while True:
        from_token = 'ETH'
        to_token = 'NEW'
        amount_from = 0.005
        amount_to = 0.005

        anvu_swap = AnvuSwap(private_key=private_key,
                             from_token=from_token,
                             to_token=to_token,
                             amount_from=amount_from,
                             amount_to=amount_to,
                             swap_all_balance=False)
        await anvu_swap.swap()


async def process_fibrous_swap(private_key: str, count_swaps, number) -> None:
    while count_swaps >= 2:
        from_token = 'ETH'
        to_token = random.choice(fibrous_swap_with_tokens)
        amount_from = fibrous_amount_eth[0]
        amount_to = fibrous_amount_eth[1]

        fibrous_swap = FibrousSwap(private_key=private_key,
                                   from_token=from_token,
                                   to_token=to_token,
                                   amount_from=amount_from,
                                   amount_to=amount_to,
                                   swap_all_balance=False)
        logger.info(f'Аккаунт {number}: Свапаю на FibrousSwap...')
        await fibrous_swap.swap()
        await sleep(40)
        from_token = to_token
        to_token = 'ETH'
        fibrous_swap = FibrousSwap(private_key=private_key,
                             from_token=from_token,
                             to_token=to_token,
                             amount_from=amount_from,
                             amount_to=amount_to,
                             swap_all_balance=True)
        logger.info(f'Аккаунт {number}: Свапаю на AnvuSwap {from_token} to {to_token}...')
        await fibrous_swap.swap()
        await sleep(40)
        count_swaps -= 2


async def process_jedi_liq(private_key: str, count_swaps, number) -> None:
    token = 'ETH'
    token2 = jediswap_token_add_liq
    amount_from = jediswap_add_liq_amount[0]
    amount_to = jediswap_add_liq_amount[1]
    jedi_liq = JediLiquidity(private_key=private_key,
                             token=token,
                             token2=token2,
                             amount_from=amount_from,
                             amount_to=amount_to)
    logger.info(f'Аккаунт {number}: Добавляю ликвидность на JediSwap ETH - {token2}...')
    await jedi_liq.add_liquidity()


async def process_jedi_liq_remove(private_key: str, count_swaps, number) -> None:
    from_token_pair = jediswap_token_remove_liq
    jedi_liq_remove = JediLiquidityRemove(private_key=private_key,
                                          from_token_pair=from_token_pair,
                                          remove_all=True,
                                          removing_percentage=0)
    logger.info(f'Аккаунт {number}: Удаляю ликвидность с JediSwap ETH - {from_token_pair}...')
    await jedi_liq_remove.remove_liquidity()


async def process_myswap_liq(private_key: str, count_swaps, number) -> None:
    token = 'ETH'
    token2 = myswap_token_add_liq
    amount_from = myswap_add_liq_amount[0]
    amount_to = myswap_add_liq_amount[1]
    myswap_liq = MySwapLiquidity(private_key=private_key,
                                 token=token,
                                 token2=token2,
                                 amount_from=amount_from,
                                 amount_to=amount_to)
    logger.info(f'Аккаунт {number}: Добавляю ликвидность на MySwap ETH - {token2}...')
    await myswap_liq.add_liquidity()


async def process_myswap_liq_remove(private_key: str, count_swaps, number) -> None:
    from_token_pair = myswap_token_remove_liq
    removing_percentage = 0
    myswap_liq_remove = MySwapLiquidityRemove(private_key=private_key,
                                              from_token_pair=from_token_pair,
                                              remove_all=True,
                                              removing_percentage=removing_percentage)
    logger.info(f'Аккаунт {number}: Удаляю ликвидность с MySwap ETH - {from_token_pair}...')
    await myswap_liq_remove.remove_liquidity()


async def process_sith_liq(private_key: str, count_swaps, number) -> None:
    token = 'ETH'
    token2 = sith_token_add_liq
    amount_from = sith_add_liq_amount[0]
    amount_to = sith_add_liq_amount[1]
    sith_liq = SithSwapLiquidity(private_key=private_key,
                                 token=token,
                                 token2=token2,
                                 amount_from=amount_from,
                                 amount_to=amount_to)
    logger.info(f'Аккаунт {number}: Добавляю ликвидность на SithSwap ETH - {sith_token_add_liq}...')
    await sith_liq.add_liquidity()


async def process_sith_liq_remove(private_key: str, count_swaps, number) -> None:
    from_token_pair = sith_token_remove_liq
    sith_liq_remove = SithLiquidityRemove(private_key=private_key,
                                          from_token_pair=from_token_pair,
                                          remove_all=True,
                                          removing_percentage=0)
    logger.info(f'Аккаунт {number}: Удаляю ликвидность с SithSwap ETH - {sith_token_remove_liq}...')
    await sith_liq_remove.remove_liquidity()


async def process_starknet_id(private_key: str, metamask_key, number):
    print(private_key)
    count_mints = random.randint(stark_id_count_mints[0], stark_id_count_mints[1])
    for i in range(1, count_mints+1):
        contract = Contract(
            address=0x05DBDEDC203E92749E2E746E2D40A768D966BD243DF04A6B712E222BC040A9AF,
            abi=MINT_ID_ABI,
            provider=get_account(private_key),
            cairo_version=1
        )
        invocation = await contract.functions["mint"].invoke(random.randint(400000, 20000000), auto_estimate=True)
        logger.info(f"Аккаунт {number}: Минчу старкнет ID. {i} раз")
        await invocation.wait_for_acceptance()
        logger.success(f"Аккаунт {number}: Транзакция выполнена! {i} раз")


async def process_k10_liq(private_key: str, count_swaps, number) -> None:
    token = 'ETH'
    token2 = k10_token_add_liq
    amount_from = k10_add_liq_amount[0]
    amount_to = k10_add_liq_amount[1]
    k10_liq = K10Liquidity(private_key=private_key,
                           token=token,
                           token2=token2,
                           amount_from=amount_from,
                           amount_to=amount_to)
    logger.info(f'Аккаунт {number}: Добавляю ликвидность 10k Swap ETH - {token2}...')
    await k10_liq.add_liquidity()


async def process_k10_liq_remove(private_key: str, count_swaps, number) -> None:
    from_token_pair = k10_token_remove_liq
    k10_liq_remove = K10LiquidityRemove(private_key=private_key,
                                        from_token_pair=from_token_pair,
                                        remove_all=True,
                                        removing_percentage=0)
    logger.info(f'Аккаунт {number}: Удаляю ликвидность с 10k Swap ETH - {from_token_pair}...')
    await k10_liq_remove.remove_liquidity()


async def process_zklend_liq(private_key: str, count_swaps, number) -> None:
    token = zklend_add_liq_token
    amount = zklend_add_token_amount - random.randint(1, 5)*zklend_add_token_amount / 100
    zklend_liq = ZKLendLiquidity(private_key=private_key,
                                 token=token,
                                 amount_from=amount,
                                 amount_to=amount)
    logger.info(f'Аккаунт {number}: Добавляю ликвидность на ZkLend в {zklend_add_liq_token}...')
    await zklend_liq.add_liquidity()


async def process_zklend_liq_remove(private_key: str, count_swaps, number) -> None:
    zklend_liq_remove = ZKLendLiquidityRemove(private_key=private_key,
                                              token=zklend_remove_liq_token,
                                              remove_all=False,
                                              removing_percentage=zklend_removing_percentage)
    logger.info(f'Аккаунт {number}: Удаляю ликвидность с ZkLend из {zklend_remove_liq_token}...')
    await zklend_liq_remove.remove_liquidity()
