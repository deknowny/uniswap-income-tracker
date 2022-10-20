import asyncio
import dataclasses

import loguru
import vkquick as vq


from src.blockchain.providers import w3s
from src.blockchain.uniswap.position import Position
from src.users import USERS


pkg = vq.Package()


@dataclasses.dataclass
class PositionReport:
    nft_token_id: int
    network: str
    token0_symbol: str
    token1_symbol: str
    price0: float
    price1: float
    liquidity0_amount: float
    liquidity1_amount: float
    liquidity_in_usd: float
    fee0_amount: float
    fee1_amount: float
    fee_in_usd: float
    total_usd: float

    def render(self) -> str:
        message = f"[ {self.network} ({self.nft_token_id}) ] "
        message += f"\n-> Pair: {self.token0_symbol}/{self.token1_symbol}"
        message += f"\n-> Price: {self.price0:.7f}/{self.price1:.7f}"
        message += (
            f"\n-> Liquidity: {self.liquidity0_amount:.5f}/{self.liquidity1_amount:.5f}"
        )
        message += f"\n-> Fees: {self.fee0_amount:.5f}/{self.fee1_amount:.5f}"
        message += f"\n-> $ Liquidity: ${self.liquidity_in_usd:.2f}"
        message += f"\n-> $ Fees: ${self.fee_in_usd:.2f}"
        message += f"\n-> $ Total: ${self.total_usd:.2f}"
        message += "\n"

        return message


@dataclasses.dataclass
class TrackingReport:
    positions: list[PositionReport]
    total_fee_in_usd: float
    total_locked_in_usd: float
    total_awaited_in_usd: float
    total_balance_in_usd: float

    def render(self) -> str:
        message = "\n\n".join(pos.render() for pos in self.positions)
        message += "\n\n[ TOTAL ]"
        message += f"\n--> $ Fees: ${self.total_fee_in_usd:.2f}"
        message += f"\n--> $ Locked: ${self.total_locked_in_usd:.2f}"
        message += f"\n--> $ Awaited: ${self.total_awaited_in_usd:.2f}"
        message += f"\n--> $ Balance: ${self.total_balance_in_usd:.2f}"
        message += f"\n--> $ Total: ${self.total_awaited_in_usd + self.total_balance_in_usd:.2f}"

        return message


@pkg.on_clicked_button()
@pkg.command("track")
async def track(ctx: vq.NewMessage):
    in_progress = await ctx.reply("Fetching...")
    account_address = USERS[str(ctx.msg.from_id)]["address"]
    total_fee_in_usd = 0
    total_locked_in_usd = 0
    total_balance_in_usd = 0

    position_reports = []
    for network in w3s:
        total_balance_in_usd_task = asyncio.create_task(
            network.fetch_assets_balance_in_usd(account_address)
        )
        positions = await Position.fetch_all(network, account_address)
        for position in positions:
            if position.liquidity > 0:
                fees, prices, own_liquidity, tokens = await asyncio.gather(
                    position.calc_fees(network),
                    position.calc_prices(network),
                    position.calc_own_liquidity(network),
                    position.fetch_tokens(network),
                )
                total_fee_in_usd += fees.token0_usd + fees.token1_usd
                total_locked_in_usd += (
                    own_liquidity.token0_usd + own_liquidity.token1_usd
                )
                position_report = PositionReport(
                    nft_token_id=position.self_nft_token,
                    network=network.network,
                    token0_symbol=tokens.token0.symbol,
                    token1_symbol=tokens.token1.symbol,
                    price0=prices.token0,
                    price1=prices.token1,
                    liquidity0_amount=own_liquidity.token0,
                    liquidity1_amount=own_liquidity.token1,
                    liquidity_in_usd=own_liquidity.token0_usd
                    + own_liquidity.token1_usd,
                    fee0_amount=fees.token0,
                    fee1_amount=fees.token1,
                    fee_in_usd=fees.token0_usd + fees.token1_usd,
                    total_usd=fees.token0_usd
                    + fees.token1_usd
                    + own_liquidity.token0_usd
                    + own_liquidity.token1_usd,
                )
                position_reports.append(position_report)

        total_balance_in_usd += await total_balance_in_usd_task

    report = TrackingReport(
        positions=position_reports,
        total_fee_in_usd=total_fee_in_usd,
        total_locked_in_usd=total_locked_in_usd,
        total_balance_in_usd=total_balance_in_usd,
        total_awaited_in_usd=total_fee_in_usd + total_locked_in_usd,
    )

    kb = vq.Keyboard(
        vq.Button.text("Tracker").primary().on_click(track), one_time=False
    )
    await in_progress.edit(report.render(), keyboard=kb)
