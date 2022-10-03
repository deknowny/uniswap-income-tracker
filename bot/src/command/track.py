import collections
import dataclasses
import math
import os
import itertools
import datetime

import vkquick as vq
import web3
import web3.eth
import web3.exceptions

from src.users import USERS


with open("erc20.json") as abi_file:
    erc20_abi = abi_file.read()

with open("factory.json") as abi_file:
    factory_abi = abi_file.read()

with open("pool.json") as abi_file:
    pool_abi = abi_file.read()


@dataclasses.dataclass
class Token:
    symbol: str
    decimals: int

    @classmethod
    def fetch(cls, address: str, w3: web3.Web3) -> "Token":
        contract = w3.eth.contract(address=address, abi=erc20_abi)
        return Token(
            symbol=contract.functions.symbol().call(),
            decimals=contract.functions.decimals().call(),
        )


@dataclasses.dataclass
class NetworkProvider:
    network: str
    provider: web3.Web3


@dataclasses.dataclass
class PositionData:
    id: int
    token0: str
    token1: str
    liquidity: int
    tick_lower: int
    tick_upper: int
    fee_growth_inside_0_last_x128: int
    fee_growth_inside_1_last_x128: int
    token_owed_0: int
    token_owed_1: int
    fee: int

    @classmethod
    def fetch_positions(
        cls, address: str, contract: web3.eth.Contract
    ) -> "list[PositionData]":
        data = []
        for i in itertools.count(0):
            try:
                token = contract.functions.tokenOfOwnerByIndex(address, i).call()

                position = contract.functions.positions(token).call()
                data.append(
                    PositionData(
                        id=token,
                        token0=position[2],
                        token1=position[3],
                        liquidity=position[7],
                        tick_lower=position[5],
                        tick_upper=position[6],
                        fee_growth_inside_0_last_x128=position[8],
                        fee_growth_inside_1_last_x128=position[9],
                        token_owed_0=position[10],
                        token_owed_1=position[11],
                        fee=position[4],
                    )
                )
            except web3.exceptions.ContractLogicError:
                break
        return data


pkg = vq.Package()
w3s = [
    NetworkProvider(
        network="Ethereum L1",
        provider=web3.Web3(web3.HTTPProvider(
            os.getenv("INFURA_L1_RPC_URL")
        ))
    ),
    NetworkProvider(
        network="Arbitrum One L2",
        provider=web3.Web3(web3.HTTPProvider(os.getenv("INFURA_ARBITRUM_RPC_URL"))),
    )
]
with open("abi.json") as abi_file:
    position_abi = abi_file.read()


@pkg.on_clicked_button()
@pkg.command("track")
async def track(ctx: vq.NewMessage):
    in_progress = await ctx.reply("Calc...")
    totals = collections.defaultdict(lambda: 0)
    message = f"[{datetime.datetime.now().isoformat()}]"
    for network in w3s:
        positions = PositionData.fetch_positions(
            address=USERS[str(ctx.msg.from_id)]["address"],
            contract=network.provider.eth.contract(  # noqa
                "0xC36442b4a4522E871399CD717aBDD847Ab11FE88",  # position manager
                abi=position_abi,
            ),
        )

        positions = [pos for pos in positions if pos.liquidity > 0]
        if positions:
            message += f"\n\nNetwork: {network.network}"
        for position in positions:
            message += f"\n-> Position: {position.id}"

            token0 = Token.fetch(address=position.token0, w3=network.provider)
            token1 = Token.fetch(address=position.token1, w3=network.provider)

            factory_contract = network.provider.eth.contract(  # noqa
                "0x1F98431c8aD98523631AE4a59f267346ea31F984", abi=factory_abi  # factory
            )
            pool_address = factory_contract.functions.getPool(
                position.token0, position.token1, position.fee
            ).call()
            pool_contract = network.provider.eth.contract(pool_address, abi=pool_abi)
            sqrt_price_x96 = pool_contract.functions.slot0().call()[0]

            price0 = math.sqrt(position.liquidity / (sqrt_price_x96**2 / 2**192))
            price1 = math.sqrt(position.liquidity / (2**192 / sqrt_price_x96**2))

            price0 = sqrt_price_x96**2 * (10**token0.decimals/10**token1.decimals) / 2 ** 192
            price1 = 1 / price0

            fee_growth_global_0_x128 = (
                pool_contract.functions.feeGrowthGlobal0X128().call()
            )
            fee_growth_global_1_x128 = (
                pool_contract.functions.feeGrowthGlobal1X128().call()
            )

            tick_lower_data = pool_contract.functions.ticks(position.tick_lower).call()
            fee_growth_outside_0_x128_lower = tick_lower_data[2]
            fee_growth_outside_1_x128_lower = tick_lower_data[3]

            tick_upper_data = pool_contract.functions.ticks(position.tick_upper).call()
            fee_growth_outside_0_x128_upper = tick_upper_data[2]
            fee_growth_outside_1_x128_upper = tick_upper_data[3]

            if (
                fee_growth_global_0_x128
                - fee_growth_outside_0_x128_lower
                - fee_growth_outside_0_x128_upper
                - position.fee_growth_inside_0_last_x128
                < 0
            ):
                token0_fee = (
                    (
                        (
                            fee_growth_global_0_x128
                            + 2**256
                            - fee_growth_outside_0_x128_lower
                            - fee_growth_outside_0_x128_upper
                            - position.fee_growth_inside_0_last_x128
                        )
                        / (2**128)
                    )
                    * position.liquidity
                    / (1 * 10**token0.decimals)
                )
                token1_fee = (
                    (
                        (
                            fee_growth_global_1_x128
                            + 2**256
                            - fee_growth_outside_1_x128_lower
                            - fee_growth_outside_1_x128_upper
                            - position.fee_growth_inside_1_last_x128
                        )
                        / (2**128)
                    )
                    * position.liquidity
                    / (1 * 10**token1.decimals)
                )
            else:
                token0_fee = (
                    (
                        (
                            fee_growth_global_0_x128
                            - fee_growth_outside_0_x128_lower
                            - fee_growth_outside_0_x128_upper
                            - position.fee_growth_inside_0_last_x128
                        )
                        / (2**128)
                    )
                    * position.liquidity
                    / (1 * 10**token0.decimals)
                )
                token1_fee = (
                    (
                        (
                            fee_growth_global_1_x128
                            - fee_growth_outside_1_x128_lower
                            - fee_growth_outside_1_x128_upper
                            - position.fee_growth_inside_1_last_x128
                        )
                        / (2**128)
                    )
                    * position.liquidity
                    / (1 * 10**token1.decimals)
                )

            message += f"\n---> {token0.symbol}: {token0_fee:.5f}"
            message += f"\n---> {token1.symbol}: {token1_fee:.5f}"
            message += f"\n -> INCOME0: {token0_fee * price0 + token1_fee:.5f}"
            message += f"\n -> INCOME1: {token1_fee * price1 + token0_fee:.5f}"
            message += f"\nPrice: {price0:.7f}/{price1:.7f}"
            totals[f"{token0.symbol}-{token1.symbol}"] += token0_fee * price0 + token1_fee
            totals[f"{token1.symbol}-{token0.symbol}"] += token1_fee * price1 + token0_fee

    message += "\n\n[ TOTALS ]"
    for key, value in totals.items():
        message += f"\n{key}: {value:.5f}"

    kb = vq.Keyboard(
        vq.Button.text("Tracker").primary().on_click(track),
        one_time=False
    )
    await in_progress.edit(message, keyboard=kb)
