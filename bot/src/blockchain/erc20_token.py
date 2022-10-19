from __future__ import annotations
import dataclasses

import web3
import eth_typing

import src.blockchain.abi
from src.blockchain.contracts import ERC20TokenContract


cache = {}


@dataclasses.dataclass
class ERC20Token:
    symbol: str
    decimals: int

    @classmethod
    async def fetch(cls, w3: web3.Web3, address: str) -> ERC20Token:
        if address in cache:
            return cache[address]
        token = ERC20TokenContract.connect(w3, address)
        inst = ERC20Token(
            symbol=await token.contract.functions.symbol().call(),
            decimals=await token.contract.functions.decimals().call(),
        )
        cache[address] = inst
        return inst
