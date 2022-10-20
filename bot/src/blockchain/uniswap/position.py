from __future__ import annotations

import asyncio
import dataclasses
import itertools
import math

import web3
import web3.exceptions

from src.blockchain.contracts import (
    NonfungiblePositionManagerContract,
    UniswapV3FactoryContract,
    UniswapV3PoolContract,
)
from src.blockchain.erc20_token import ERC20Token
from src.blockchain.providers import NetworkProvider
from src.blockchain.uniswap.in_usd_amount import calc_amount_in_usd


@dataclasses.dataclass
class Position:
    nonce: int
    operator: str
    token0: str
    token1: str
    fee: int
    tick_lower: int
    tick_upper: int
    liquidity: int
    fee_growth_inside_0_last_x128: int
    fee_growth_inside_1_last_x128: int
    token_owed_0: int
    token_owed_1: int
    self_nft_token: int

    async def calc_prices(self, provider: NetworkProvider) -> PositionPrices:
        erc20_token0 = await ERC20Token.fetch(provider, self.token0)
        erc20_token1 = await ERC20Token.fetch(provider, self.token1)

        # Fetch liquidity pool for calculating
        factory = UniswapV3FactoryContract.static_connect(provider.provider)
        pool_address = await factory.contract.functions.getPool(
            self.token0, self.token1, self.fee
        ).call()
        pool = UniswapV3PoolContract.connect(provider.provider, pool_address)

        sqrt_price_x96 = (await pool.contract.functions.slot0().call())[0]
        price0 = (
            sqrt_price_x96**2
            * (10**erc20_token0.decimals / 10**erc20_token1.decimals)
            / 2**192
        )
        return PositionPrices(token0=price0, token1=1 / price0)

    async def fetch_tokens(self, provider: NetworkProvider) -> PositionTokens:
        # Fetch tokens' info
        erc20_token0 = await ERC20Token.fetch(provider, self.token0)
        erc20_token1 = await ERC20Token.fetch(provider, self.token1)
        return PositionTokens(token0=erc20_token0, token1=erc20_token1)

    async def calc_own_liquidity(self, provider: NetworkProvider) -> PositionLiquidity:
        # Fetch tokens' info
        erc20_token0 = await ERC20Token.fetch(provider, self.token0)
        erc20_token1 = await ERC20Token.fetch(provider, self.token1)

        # Fetch liquidity pool for calculating
        factory = UniswapV3FactoryContract.static_connect(provider.provider)
        pool_address = await factory.contract.functions.getPool(
            self.token0, self.token1, self.fee
        ).call()
        pool = UniswapV3PoolContract.connect(provider.provider, pool_address)

        current_tick = (await pool.contract.functions.slot0().call())[1]
        pa = math.sqrt(1.0001**self.tick_lower)
        pb = math.sqrt(1.0001**self.tick_upper)
        p = math.sqrt(1.0001**current_tick)
        token0 = self.liquidity * (pb - p) / (p * pb)
        token1 = self.liquidity * (p - pa)
        token0 = token0 / (10**erc20_token0.decimals)
        token1 = token1 / (10**erc20_token1.decimals)
        token0_usd, token1_usd = await asyncio.gather(
            calc_amount_in_usd(provider, self.token0, token0, self.fee),
            calc_amount_in_usd(provider, self.token1, token1, self.fee),
        )
        return PositionLiquidity(
            token0=token0,
            token1=token1,
            token0_usd=token0_usd,
            token1_usd=token1_usd,
        )

    async def calc_fees(self, provider: NetworkProvider) -> PositionFees:
        # Fetch tokens' info
        erc20_token0 = await ERC20Token.fetch(provider, self.token0)
        erc20_token1 = await ERC20Token.fetch(provider, self.token1)

        # Fetch liquidity pool for calculating
        factory = UniswapV3FactoryContract.static_connect(provider.provider)
        pool_address = await factory.contract.functions.getPool(
            self.token0, self.token1, self.fee
        ).call()
        pool = UniswapV3PoolContract.connect(provider.provider, pool_address)

        (
            fee_growth_global_0_x128,
            fee_growth_global_1_x128,
            tick_lower_data,
            tick_upper_data,
        ) = await asyncio.gather(
            pool.contract.functions.feeGrowthGlobal0X128().call(),
            pool.contract.functions.feeGrowthGlobal1X128().call(),
            pool.contract.functions.ticks(self.tick_lower).call(),
            pool.contract.functions.ticks(self.tick_upper).call(),
        )
        fee_growth_outside_0_x128_lower = tick_lower_data[2]
        fee_growth_outside_1_x128_lower = tick_lower_data[3]
        fee_growth_outside_0_x128_upper = tick_upper_data[2]
        fee_growth_outside_1_x128_upper = tick_upper_data[3]

        if (
            fee_growth_global_0_x128
            - fee_growth_outside_0_x128_lower
            - fee_growth_outside_0_x128_upper
            - self.fee_growth_inside_0_last_x128
            < 0
        ):
            token0_fee = (
                (
                    (
                        fee_growth_global_0_x128
                        + 2**256
                        - fee_growth_outside_0_x128_lower
                        - fee_growth_outside_0_x128_upper
                        - self.fee_growth_inside_0_last_x128
                    )
                    / (2**128)
                )
                * self.liquidity
                / (1 * 10**erc20_token0.decimals)
            )
            token1_fee = (
                (
                    (
                        fee_growth_global_1_x128
                        + 2**256
                        - fee_growth_outside_1_x128_lower
                        - fee_growth_outside_1_x128_upper
                        - self.fee_growth_inside_1_last_x128
                    )
                    / (2**128)
                )
                * self.liquidity
                / (1 * 10**erc20_token1.decimals)
            )
        else:
            token0_fee = (
                (
                    (
                        fee_growth_global_0_x128
                        - fee_growth_outside_0_x128_lower
                        - fee_growth_outside_0_x128_upper
                        - self.fee_growth_inside_0_last_x128
                    )
                    / (2**128)
                )
                * self.liquidity
                / (1 * 10**erc20_token0.decimals)
            )
            token1_fee = (
                (
                    (
                        fee_growth_global_1_x128
                        - fee_growth_outside_1_x128_lower
                        - fee_growth_outside_1_x128_upper
                        - self.fee_growth_inside_1_last_x128
                    )
                    / (2**128)
                )
                * self.liquidity
                / (1 * 10**erc20_token1.decimals)
            )

        return PositionFees(
            token0=token0_fee,
            token1=token1_fee,
            token0_usd=await calc_amount_in_usd(provider, self.token0, token0_fee, self.fee),
            token1_usd=await calc_amount_in_usd(provider, self.token1, token1_fee, self.fee),
        )

    @classmethod
    async def fetch_all(
        cls,
        provider: NetworkProvider,
        account_address: str,
    ) -> list[Position]:
        positions = []
        position_manager = NonfungiblePositionManagerContract.static_connect(provider.provider)
        for i in itertools.count(0):
            try:
                nft_token = (
                    await position_manager.contract.functions.tokenOfOwnerByIndex(
                        account_address, i
                    ).call()
                )
                position = await position_manager.contract.functions.positions(
                    nft_token
                ).call()
                positions.append(
                    Position(
                        nonce=position[0],
                        operator=position[1],
                        token0=position[2],
                        token1=position[3],
                        fee=position[4],
                        tick_lower=position[5],
                        tick_upper=position[6],
                        liquidity=position[7],
                        fee_growth_inside_0_last_x128=position[8],
                        fee_growth_inside_1_last_x128=position[9],
                        token_owed_0=position[10],
                        token_owed_1=position[11],
                        self_nft_token=nft_token,
                    )
                )
            except web3.exceptions.ContractLogicError:
                break
        return positions


@dataclasses.dataclass
class PositionFees:
    token0: float
    token1: float

    token0_usd: float
    token1_usd: float


@dataclasses.dataclass
class PositionPrices:
    token0: float
    token1: float


@dataclasses.dataclass
class PositionLiquidity:
    token0: float
    token1: float

    token0_usd: float
    token1_usd: float


@dataclasses.dataclass
class PositionTokens:
    token0: ERC20Token
    token1: ERC20Token
