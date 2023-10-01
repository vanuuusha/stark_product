import threading
import time
import random
import copy
from okx import okx_withdraw_func
from loguru import logger
import sys
logger.remove()
logger.add(sys.stdout, format="{time}: {message}")
from config import *
from src.utils.mappings import module_handlers
from src.utils.helper import (
    private_keys,
    active_module,
    metamask_keys,
    withdraw_address,
    okx_withdraw_stark
)
from deploy import deploy_account
from helper import calculate_address
import re
import asyncio


def process_private_key(private_key_num: int, thread_num: int):
    modules = copy.copy(active_module)
    random.shuffle(modules)
    if okx_withdraw:
        amount = okx_withdraw_amount - okx_withdraw_amount * random.randint(1, 5) / 100
        private_key = private_keys[private_key_num]
        private_key = re.sub(r'[^0-9a-fA-F]+', '', private_key)
        private_key = int(private_key, 16)
        address = calculate_address(private_key)
        logger.info(f'Аккаунт {private_key_num}: Начинаю процесс вывода ETH на кошелек {address}')
        time.sleep(random.randint(5, 10))
        okx_withdraw_func(address, amount, number=private_key_num)
        time.sleep(40)

    if DEPLOY:
        asyncio.run(deploy_account(private_keys[private_key_num]))
        time.sleep(100)

    for module in modules[:]:
        if 'remove_liq' in module:
            add_module = module.replace('remove', 'add')
            if add_module in modules:
                modules.remove(module)
                add_module_index = modules.index(add_module)
                modules.insert(add_module_index+1, module)

    zklend_count = random.randint(zklend_count_actions[0], zklend_count_actions[1])
    if 'zklend_add_liq' in modules and 'zklend_remove_liq' in modules and zklend_count != 1:
        modules.remove('zklend_remove_liq')
        index = modules.index('zklend_add_liq')
        modules.remove('zklend_add_liq')
        for i in range(0, zklend_count*2, 2):
            modules.insert(index + i, 'zklend_add_liq')
            modules.insert(index + i + 1, 'zklend_remove_liq')

    temp = 0
    for module in modules[:]:
        if 'return' in module:
            temp += 1
            modules.remove(module)
            modules.append(module)

    if temp == 2:
        modules.pop()

    for pattern in modules:
        if pattern == 'jediswap_swap':
            count_swaps = random.randint(jediswap_swap_count_swaps[0], jediswap_swap_count_swaps[1])
        elif pattern == 'myswap_swap':
            count_swaps = random.randint(myswap_swap_count_swaps[0], myswap_swap_count_swaps[1])
        elif pattern == 'k10_swap':
            count_swaps = random.randint(k10_swap_count_swaps[0], k10_swap_count_swaps[1])
        elif pattern == 'sith_swap':
            count_swaps = random.randint(sith_swap_count_swaps[0], sith_swap_count_swaps[1])
        elif pattern == 'anvu_swap':
            count_swaps = random.randint(avnu_swap_count_swaps[0], avnu_swap_count_swaps[1])
        elif pattern == 'fibrous_swap':
            count_swaps = random.randint(fibrous_swap_count_swaps[0], fibrous_swap_count_swaps[1])
        elif pattern == 'dmail':
            count_swaps = random.randint(dmail_count_tx[0], dmail_count_tx[1])
        else:
            count_swaps = 0
        if count_swaps % 2 == 1:
            count_swaps -= 1
        if 'return' in pattern:
            private_key = {'private_key_num': private_key_num, 'private_keys': private_keys, 'metamask_keys': metamask_keys, 'withdraw_address': withdraw_address, 'okx_withdraw_stark': okx_withdraw_stark}
        else:
            private_key = private_keys[private_key_num]

        asyncio.run(module_handlers[pattern](private_key, count_swaps, number=private_key_num))
        logger.info(f'Аккаунт {private_key_num}: Закончил выполнять задачу')
        time_to_sleep = random.randint(10, 20)
        logger.info(f'Аккаунт {private_key_num}: Засыпаю на {time_to_sleep} секунд...')
        time.sleep(time_to_sleep)


def main() -> None:
    waiter = private_keys[:]
    while waiter:
        threads = []
        for _ in range(min(NUM_THREADS, len(waiter))):
            private_key = waiter.pop()
            private_key_num = private_keys.index(private_key)
            threads.append(threading.Thread(target=process_private_key, args=(private_key_num, len(threads) + 1)))

        for proc in threads:
            proc.start()

        for proc in threads:
            proc.join()


if __name__ == '__main__':
    main()
