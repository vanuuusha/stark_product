NUM_THREADS = 1 # Сколько аккаунтов делать одновременно
MAX_FEE_FOR_TRANSACTION = 0.1 # Максимальная цена за транзакцию
RPC_URL = 'https://starknet-mainnet.infura.io/v3/3749594242f54e1c92b91c79bdaa6bbf' # получить RPC можно по ссылке https://app.infura.io/dashboard


# TODO все транзакции должны быть с балансом больше или равны 0.0001 ETH
BRAVOS = True # кошельки в wallets.txt являются бравосами?
OLD_ARGENT = False  # кошельки в wallets.txt являются старыми аргентами?
NEW_ARGENT = False  # кошельки в wallets.txt являются новыми аргентами?

DEPLOY = False # делать ли деплой

okx_proxy = ''
okx_apikey = ''
okx_secretkey = ''
okx_passphrase = ''


okx_withdraw = False # выводим из okx?
okx_withdraw_amount = 0.02 # сколько выводить из okx

okx_return_percentage = 80 # сколько процентов остатка возвращать на okx
okx_return_by_orbitter = False # возвращаем через орбиттер (и сеть ARB)?
okx_return_by_stark = False # возвращаем через старк напрямую?. Если орбиттер и старк True - выбирает случайное

#TODO jediswap
jediswap_swap = False # делаем jediswap?
jediswap_swap_count_swaps = [2, 2] # Количество транзакций в myswap (от и до)
jediswap_amount_eth = [0.01, 0.015] # Количество eth  для транзации (от и до)
jediswap_swap_with_tokens = ['USDC'] # какие токены будут использоваться, например если хотим USDC и USDT ['USDC', 'USDT']

jediswap_add_liq = False # делаем jediswap?
jediswap_add_liq_amount = [0.001, 0.002]
jediswap_token_add_liq = 'USDC'  # какой токен добавляем в ликвидность

jediswap_remove_liq = False # делаем jediswap?
jediswap_token_remove_liq = 'USDC'  # какой токен удаляем из ликвидность

# TODO dmail
dmail = True # делаем dmail?
dmail_count_tx = [2, 4] # Количество транзакций в дмайл (от и до)

#TODO stark_id
stark_id = False # делаем starknet_id?
stark_id_count_mints = [2, 2] # Количество транзакций в старкнет ид (от и до)

#TODO myswap
myswap_swap = False # делаем myswap?
myswap_swap_count_swaps = [2, 2] # Количество транзакций в myswap (от и до)
myswap_amount_eth = [0.01, 0.015] # Количество eth для транзации (от и до)
myswap_swap_with_tokens = ['USDC'] # какие токены будут использоваться, например если хотим USDC и USDT ['USDC', 'USDT']

myswap_add_liq = False # делаем myswap ликвидность (добавление)
myswap_add_liq_amount = [0.001, 0.002] # Количество eth для транзации (от и до)
myswap_token_add_liq = 'DAI' # какой токен добавляем в ликвидность

myswap_remove_liq = False # делаем myswap ликвидность (удаление)
myswap_token_remove_liq = 'DAI' # какой токен удаляем из ликвидность

#TODO k10 swap
k10_swap = False # делаем k10_swap?
k10_swap_count_swaps = [2, 2] # Количество транзакций в myswap (от и до)
k10_amount_eth = [0.01, 0.015] # Количество eth для транзации (от и до)
k10_swap_with_tokens = ['USDC', 'DAI'] # какие токены будут использоваться, например если хотим USDC и USDT ['USDC', 'USDT']

k10_add_liq = False # делаем k10_swap ликвидность (добавление)
k10_add_liq_amount = [0.001, 0.002] # Количество eth для транзации (от и до)
k10_token_add_liq = '' # какой токен добавляем в ликвидность

k10_remove_liq = False # делаем k10_swap ликвидность (удаление)
k10_token_remove_liq = ''  # какой токен удаляем из ликвидность

#TODO sith swap
sith_swap = False # делаем sith_swap?
sith_swap_count_swaps = [2, 2]  # Количество транзакций в sith_swap (от и до)
sith_amount_eth = [0.01, 0.015] # Количество eth для транзации (от и до)
sith_swap_with_tokens = ['USDC'] # какие токены будут использоваться, например если хотим USDC и USDT ['USDC', 'USDT']

sith_add_liq = False # делаем sith_swap ликвидность (добавление)
sith_add_liq_amount = [0.001, 0.002] # Количество eth для транзации (от и до)
sith_token_add_liq = '' # какой токен добавляем в ликвидность

sith_remove_liq = False # делаем sith_swap ликвидность (удаление)
sith_token_remove_liq = '' # какой токен удаляем из ликвидность

#TODO avnu swap
anvu_swap = False # делаем avnu_swap?
avnu_swap_count_swaps = [2, 2] # Количество транзакций в avnu_swap (от и до)
avnu_amount_eth = [0.01, 0.015] # Количество eth для транзации (от и до)
avnu_swap_with_tokens = ['USDC'] # какие токены будут использоваться, например если хотим USDC и USDT ['USDC', 'USDT']

#TODO fibrous swap
fibrous_swap = False # делаем fibrous_swap?
fibrous_swap_count_swaps = [2, 2] # Количество транзакций в fibrous_swap (от и до)
fibrous_amount_eth = [0.0001, 0.0001] # Количество eth для транзации (от и до)
fibrous_swap_with_tokens = ['USDC'] # какие токены будут использоваться, например если хотим USDC и USDT ['USDC', 'USDT']

# TODO zklend swap
zklend_add_liq = False # депозитим в zklend?
zklend_add_liq_token = 'ETH' # В какой токене?
zklend_add_token_amount = 0.015 # сколько депозитим

zklend_remove_liq = False # удаляем ликвидность из zklend?
zklend_remove_liq_token = 'ETH' # В какой токене?
zklend_removing_percentage = 10 # сколько процентов токенов удаляем

zklend_count_actions = [2, 4] # Количестко транзакций на zklend






























































#TODO не для изменения
zklend_removing_percentage = zklend_removing_percentage / 100
SLIPPAGE = 0.07
