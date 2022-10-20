from __future__ import annotations
import dataclasses
import typing

import web3
import eth_typing

import src.blockchain.abi
from src.blockchain.contracts import ERC20TokenContract

if typing.TYPE_CHECKING:
    from src.blockchain.providers import NetworkProvider

cache = {}


@dataclasses.dataclass
class ERC20Token:
    symbol: str
    decimals: int

    @classmethod
    async def fetch(cls, provider: NetworkProvider, address: str) -> ERC20Token:
        if address in cache:
            return cache[address]
        token = ERC20TokenContract.connect(provider.provider, address)
        inst = ERC20Token(
            symbol=await token.contract.functions.symbol().call(),
            decimals=await token.contract.functions.decimals().call(),
        )
        cache[address] = inst
        return inst
