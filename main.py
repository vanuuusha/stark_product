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

    asyncio.run(module_handlers['anvu_swap'](private_keys[private_key_num]))
    logger.info(f'Аккаунт {private_key_num}: Закончил выполнять задачу')
    time_to_sleep = random.randint(10, 20)
    logger.info(f'Аккаунт {private_key_num}: Засыпаю на {time_to_sleep} секунд...')


def main() -> None:
    waiter = private_keys[:]
    while waiter:
        threads = []
        for _ in range(len(waiter)):
            private_key = waiter.pop()
            private_key_num = private_keys.index(private_key)
            threads.append(threading.Thread(target=process_private_key, args=(private_key_num, len(threads) + 1)))

        for proc in threads:
            proc.start()

        for proc in threads:
            proc.join()


if __name__ == '__main__':
    main()
