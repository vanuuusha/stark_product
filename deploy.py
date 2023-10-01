from deployer import *
from starknet_py.net.gateway_client import GatewayClient
import asyncio
from asyncio import sleep
from starknet_py.net.networks import MAINNET
client = GatewayClient(MAINNET)


async def deploy_account(key):
    account, call_data, salt, class_hash = import_stark_account(key, client)
    while True:
        try:
            nonce = await account.get_nonce()
            if nonce > 0:
                logger.info(
                    f"[{'0x' + '0' * (66 - len(hex(account.address))) + hex(account.address)[2::]}] Уже задеплоин, пропускаю")
                return
            else:
                break
        except Exception as e:
            logger.error(
                f"[{'0x' + '0' * (66 - len(hex(account.address))) + hex(account.address)[2::]}]: {e}")
    while True:
        logger.info(f"[{'0x' + '0' * (66 - len(hex(account.address))) + hex(account.address)[2::]}] Проверяю баланс.")
        try:
            balance = await account.get_balance()
            logger.info(f"{'0x' + '0' * (66 - len(hex(account.address))) + hex(account.address)[2::]} Баланс кошелька: {balance / 1e18} ETH")
            if balance >= 1e14:
                break

        except Exception as e:
            logger.error(f"{'0x' + '0' * (66 - len(hex(account.address))) + hex(account.address)[2::]} : {e}")
    i = 0
    while i < 3:
        i += 1
        try:
            if BRAVOS:
                account_deployment_result = await deploy_account_braavos(
                    address=account.address,
                    class_hash=class_hash,
                    salt=salt,
                    key_pair=account.signer.key_pair,
                    client=account.client,
                    chain=chain,
                    constructor_calldata=call_data,
                    auto_estimate=True,
                )
            else:
                account_deployment_result = await Account.deploy_account(
                    address=account.address,
                    class_hash=class_hash,
                    salt=salt,
                    key_pair=account.signer.key_pair,
                    client=account.client,
                    chain=chain,
                    constructor_calldata=call_data,
                    auto_estimate=True,
                )
            await account_deployment_result.wait_for_acceptance()
            account = account_deployment_result.account
            logger.success(f"[{'0x' + '0' * (66 - len(hex(account.address))) + hex(account.address)[2::]}] успешный деплой, хэш: https://starkscan.co/tx/{hex(account_deployment_result.hash)}")
            await sleep(40)
            return 1

        except Exception as e:
            logger.error(f"[{'0x' + '0' * (66 - len(hex(account.address))) + hex(account.address)[2::]}] Ошибка во время деплоя, {e}")
    logger.error(f"[{'0x' + '0' * (66 - len(hex(account.address))) + hex(account.address)[2::]}] Уже задеплоин")
    return -1