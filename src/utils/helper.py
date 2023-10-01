from src.utils.mappings import (
    module_handlers
)

with open('config.py', 'r', encoding='utf-8-sig') as file:
    module_config = file.read()

exec(module_config)

private_keys, withdraw_address, metamask_keys, okx_withdraw_stark = [], [], [], []
with open('wallets.txt', 'r', encoding='utf-8-sig') as file:
    for num, line in enumerate(file):
        if num == 0:
            continue
        line = line.split('-')
        private_keys.append(line[0].strip())
        withdraw_address.append(line[1].strip())
        metamask_keys.append(line[2].strip())
        okx_withdraw_stark.append(line[3].strip())

patterns = {}

for module in module_handlers:
    if globals().get(module):
        patterns[module] = 'On'
    else:
        patterns[module] = 'Off'
print(patterns)

print(f'Загружено {len(private_keys)} кошельков')

for pattern, value in patterns.items():
    if value == 'Off':
        pass
    else:
        print(f'{pattern} = {value}')

active_module = [module for module, value in patterns.items() if value == 'On']

