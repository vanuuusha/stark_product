import random
import json
import time
from datetime import datetime
import requests
import hmac
import base64
import hashlib
import ccxt
from config import okx_proxy, okx_secretkey, okx_apikey, okx_passphrase
base_url = "https://www.okx.com"


def get_request_proxies():
    return {"http": okx_proxy, "https": okx_proxy}


def get_request_headers(method, endpoint, request_params, body='', sub_account_id=None):
    timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
    message = timestamp + method + endpoint + request_params + body
    mac = hmac.new(okx_secretkey.encode("utf-8"), message.encode("utf-8"), hashlib.sha256)
    sign = base64.b64encode(mac.digest()).decode("utf-8")

    headers = {
        "OK-ACCESS-KEY": okx_apikey,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-passphrase": okx_passphrase,
        "Content-Type": "application/json"
    }

    if sub_account_id is not None:
        headers["OK-ACCESS-SUBACCOUNT"] = sub_account_id

    return headers


def get_trading_account_balance(ccy='ETH'):
    method = "GET"
    endpoint = "/api/v5/account/balance"
    params = ""

    if ccy is not None:
        params += f"?ccy={ccy}"

    url = base_url + endpoint + params
    headers = get_request_headers(method, endpoint, params)

    try:
        response = requests.get(url, headers=headers, proxies=get_request_proxies())
        data = response.json()["data"][0]['details']
        eth_balance = data['availBal']
        return eth_balance
    except Exception as e:
        print(f"Ошибка при получении баланса торгового аккаунта: {e}")
        return []


def get_okx_withdrawal_fee(symbolWithdraw, chainName):
    exchange_options = {
        'apiKey': okx_apikey,
        'secret': okx_secretkey,
        'password': okx_passphrase,
        'enableRateLimit': True
    }

    exchange = ccxt.okx(exchange_options)

    currencies = exchange.fetch_currencies()
    for currency in currencies:
        if currency == symbolWithdraw:
            currency_info = currencies[currency]
            network_info = currency_info.get('networks', None)
            if network_info:
                for network in network_info:
                    network_data = network_info[network]
                    network_id = network_data['id']
                    if network_id == chainName:
                        withdrawal_fee = currency_info['networks'][network]['fee']
                        if withdrawal_fee == 0:
                            return 0
                        else:
                            return withdrawal_fee
    raise ValueError(f"  [OKX] Не могу найти комиссию для токена ${symbolWithdraw} в сети {chainName}")


def okx_withdraw_func(address, amount, number):
    exchange_options = {
        'apiKey': okx_apikey,
        'secret': okx_secretkey,
        'password': okx_passphrase,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot',
        }
    }
    exchange_options['proxies'] = get_request_proxies()
    exchange = ccxt.okx(exchange_options)
    currency = exchange.fetch_currencies()['ETH']['networks']
    currency = currency['Starknet']
    min_withdrawal_amount = float(currency['limits']['withdraw']['min'])
    fee = float(currency['fee'])

    if amount > min_withdrawal_amount:
        moddifier = random.randint(0, 5)
        amount = amount * (1 - moddifier / 100)
        print(f'Вывожу ETH в количестве {amount+fee}')
    else:
        raise Exception(f'Недостаточко средств на OKX (Пытаюсь вывести {amount+fee})')

    try:
        chain_name = 'ETH' + '-' + 'Starknet'
        address = str(address)[2:]
        while len(address) < 64:
            address = f'0{address}'
        address = f'0x{str(address)}'
        print('Адрес вывода', address)
        withdraw = exchange.withdraw('ETH', amount+fee, address,
            params={
                "toAddress": address,
                "chainName": chain_name,
                "dest": 4,
                "fee": fee,
                "pwd": '-',
                "amt": amount+fee,
                "network": 'Starknet'
            }
        )
        withdrawal_id = withdraw['id']
        status = "pending"
        while status == "pending":
            time.sleep(30)
            fetched_withdrawal = exchange.fetch_withdrawals()
            for fetched_withdrawal in fetched_withdrawal:
                if fetched_withdrawal['id'] == withdrawal_id:
                    status = fetched_withdrawal['status']
                    break
        if status == "ok":
            time.sleep(60)
            print('Перевод средств успешно выполнен')
        else:
            print(f'Не удалось вывести средства с биржи. Аккаунт. Сумма {amount+fee}')
    except ccxt.InvalidAddress:
        print(f'Адрес аккаунта не добавлен в вайтлист')
        raise Exception(f'Адрес {address} аккаунта не добавлен в вайтлист')
    except ccxt.InsufficientFunds:
        print(f'Для перевода на аккаунт. недостаточно средств, требуется {amount+fee}')
        raise Exception(f'Для перевода на аккаунт. недостаточно средств, требуется {amount+fee}')
    except Exception as e:
        raise Exception(f'Возникла непридвиденная ошибка, вероятно с сетью starknet ведутся технические работы')


def get_sub_accounts():
    method = "GET"
    endpoint = "/api/v5/users/subaccount/list"
    url = base_url + endpoint
    headers = get_request_headers(method, endpoint, "")

    try:
        response = requests.get(url, headers=headers, proxies=get_request_proxies())
        json_response = response.json()
        if 'data' in json_response:
            return json_response["data"]
        else:
            print(f"Ошибка при получении списка суб-аккаунтов: {json_response}")
            return []
    except Exception as e:
        print(f"Ошибка при получении списка суб-аккаунтов: {e}")
        return []


def get_sub_account_funding_balance(sub_account_id, ccy=None):
    method = "GET"
    endpoint = "/api/v5/asset/subaccount/balances"
    params = f"?subAcct={sub_account_id}"

    if ccy is not None:
        params += f"&ccy={ccy}"

    url = base_url + endpoint + params
    headers = get_request_headers(method, endpoint, params)

    try:
        response = requests.get(url, headers=headers, proxies=get_request_proxies())
        return response.json()["data"]
    except Exception as e:
        print(f"  Ошибка при получении баланса суб-аккаунта {sub_account_id}: {e}")
        return []


def transfer_to_master_account(from_sub_account, ccy, amount):
    method = "POST"
    endpoint = "/api/v5/asset/transfer"
    url = base_url + endpoint
    payload = {
        "ccy": ccy,
        "amt": amount,
        "from": "6",
        "to": "6",
        "subAcct": from_sub_account,
        "type": "2"
    }
    json_payload = json.dumps(payload)
    headers = get_request_headers(method, endpoint, "", json_payload)
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=get_request_proxies())
        response_data = response.json()
        if "data" in response_data and len(response_data["data"]) > 0:
            transfer_id = response_data["data"][0]["transId"]
            print(f"  Переведено {amount} {ccy} с суб-аккаунта {from_sub_account} на мастер-аккаунт (ID транзакции: {transfer_id})")
        elif "code" in response_data and "msg" in response_data:
            print(f"  Ошибка при переводе {amount} {ccy} с суб-аккаунта {from_sub_account} на мастер-аккаунт: {response_data['msg']} (Код ошибки: {response_data['code']})")
        else:
            print(f"  Ошибка при переводе {amount} {ccy} с суб-аккаунта {from_sub_account} на мастер-аккаунт: Неизвестная ошибка")
    except Exception as e:
        print(f"  Ошибка при переводе {amount} {ccy} с суб-аккаунта {from_sub_account} на мастер-аккаунт: {e}")


def okx_withdrawal_subs():
    sub_account_list = get_sub_accounts()

    for sub_account in sub_account_list:
        sub_account_id = sub_account["subAcct"]
        balances = get_sub_account_funding_balance(sub_account_id)
        for balance in balances:
            currency = balance["ccy"]
            available = balance["availBal"]
            transfer_to_master_account(sub_account_id, currency, available)


if __name__ == '__main__':
    okx_withdrawal_subs()