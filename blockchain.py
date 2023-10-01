from web3 import Web3
from asyncio import sleep
from loguru import logger

def wait_for_gwei():
    w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
    while True:
        gas_price = w3.eth.gas_price
        gas_price_gwei = w3.from_wei(gas_price, 'gwei')
        if gas_price_gwei >= MAX_GWEI:
            logger.info('Газ слишком дорог, ожидаю')
            sleep(10)
        else:
            break
        return gas_price_gwei