import re
from config import BRAVOS, OLD_ARGENT, NEW_ARGENT
from starknet_py.net.signer.stark_curve_signer import (
    KeyPair,
)
from starknet_py.hash.address import compute_address


def calculate_address(private_key):
    if sum(map(int, [BRAVOS, OLD_ARGENT, NEW_ARGENT])) >= 2:
        raise Exception

    key_pair = KeyPair.from_private_key(private_key)
    if BRAVOS:
        proxy_class_hash = 0x03131fa018d520a037686ce3efddeab8f28895662f019ca3ca18a626650f7d1e
        implementation_class_hash = 0x5aa23d5bb71ddaa783da7ea79d405315bafa7cf0387a74f4593578c3e9e6570
        selector = 0x2dd76e7ad84dbed81c314ffe5e7a7cacfb8f4836f01af4e913f275f89a3de1a

        calldata = [key_pair.public_key]
        address = compute_address(class_hash=proxy_class_hash,
                                  constructor_calldata=[implementation_class_hash, selector, len(calldata), *calldata],
                                  salt=key_pair.public_key)
    elif NEW_ARGENT:
        address = compute_address(class_hash=0x01a736d6ed154502257f02b1ccdf4d9d1089f80811cd6acad48e6b6a9d1f2003,
                                  constructor_calldata=[key_pair.public_key, 0],
                                  salt=key_pair.public_key)
    elif OLD_ARGENT:
        proxy_class_hash = 0x025ec026985a3bf9d0cc1fe17326b245dfdc3ff89b8fde106542a3ea56c5a918
        implementation_class_hash = 0x33434ad846cdd5f23eb73ff09fe6fddd568284a0fb7d1be20ee482f044dabe2
        selector = 0x79dc0da7c54b95f10aa182ad0a46400db63156920adb65eca2654c0945a463

        calldata = [key_pair.public_key, 0]
        address = compute_address(class_hash=proxy_class_hash,
                                  constructor_calldata=[implementation_class_hash, selector, len(calldata), *calldata],
                                  salt=key_pair.public_key)
    return hex(address)
