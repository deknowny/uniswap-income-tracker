from __future__ import annotations

import math
import typing

import loguru
import web3

from src.blockchain.contracts import UniswapV3FactoryContract, UniswapV3PoolContract
from src.blockchain.erc20_token import ERC20Token

if typing.TYPE_CHECKING:
    from src.blockchain.providers import NetworkProvider


async def calc_amount_in_usd(
    provider: NetworkProvider, token_address: str, amount: float, fee: int
) -> float:
    # Fetch tokens' info
    erc20_token0 = await ERC20Token.fetch(provider, token_address)
    if erc20_token0.symbol in {"USDC", "DAI", "USDT"}:
        return amount
    erc20_token1 = await ERC20Token.fetch(
        provider, provider.usd_stablecoin_address
    )

    # Fetch liquidity pool for calculating
    factory = UniswapV3FactoryContract.static_connect(provider.provider)
    pool_address = await factory.contract.functions.getPool(
        token_address, provider.usd_stablecoin_address, fee
    ).call()
    pool = UniswapV3PoolContract.connect(provider.provider, pool_address)

    sqrt_price_x96 = (await pool.contract.functions.slot0().call())[0]
    price_x96 = sqrt_price_x96**2
    if math.log(price_x96, 2) > 192:
        price_x96 = 2**192 / (price_x96 / 2**192)
    price0 = (
        price_x96
        * (10**erc20_token0.decimals / 10**erc20_token1.decimals)
        / 2**192
    )
    loguru.logger.info(str((erc20_token0, erc20_token1, price0, sqrt_price_x96, )))
    return price0 * amount
