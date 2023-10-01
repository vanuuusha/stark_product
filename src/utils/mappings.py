from src.utils.runner import *

module_handlers = {
    'jediswap_swap': process_jediswap_swap,
    'myswap_swap': process_myswap_swap,
    'k10_swap': process_k10_swap,
    'sith_swap': process_sith_swap,
    'anvu_swap': process_anvu_swap,
    'fibrous_swap': process_fibrous_swap,
    'jediswap_add_liq': process_jedi_liq,
    'jediswap_remove_liq': process_jedi_liq_remove,
    'myswap_add_liq': process_myswap_liq,
    'myswap_remove_liq': process_myswap_liq_remove,
    'sith_add_liq': process_sith_liq,
    'sith_remove_liq': process_sith_liq_remove,
    'k10_add_liq': process_k10_liq,
    'k10_remove_liq': process_k10_liq_remove,
    'zklend_add_liq': process_zklend_liq,
    'zklend_remove_liq': process_zklend_liq_remove,
    'okx_return_by_orbitter': process_orbiter_bridging,
    'okx_return_by_stark': process_okx_withdraw_stark,
    'stark_id': process_starknet_id,
    'dmail': process_dmail,
}
