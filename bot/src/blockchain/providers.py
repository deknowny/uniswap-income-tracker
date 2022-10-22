import dataclasses
import enum

import loguru
import web3.eth
import web3.net

import src.envs
from src.blockchain.contracts import ERC20TokenContract
from src.blockchain.erc20_token import ERC20Token
from src.blockchain.uniswap.in_usd_amount import calc_amount_in_usd


class NetworkLabel(str, enum.Enum):
    L1 = "L1"
    ARBITRUM = "ARBITRUM"


@dataclasses.dataclass
class NetworkProvider:
    network: str
    network_label: str
    provider: web3.Web3
    assets: list[str]
    usd_stablecoin_address: str
    weth_address: str

    async def fetch_assets_balance_in_usd(self, address: str) -> float:
        total_usd = 0
        eth_balance = await self.provider.eth.get_balance(address)
        total_usd += await calc_amount_in_usd(
            self,
            self.weth_address,  # WETH
            eth_balance / 10**18,
            3000
        )
        for asset_address in self.assets:
            asset_contract = ERC20TokenContract.connect(self.provider, asset_address)
            asset_balance = await asset_contract.contract.functions.balanceOf(
                address
            ).call()
            asset_token = await ERC20Token.fetch(self, asset_address)
            total_usd += await calc_amount_in_usd(
                self, asset_address,
                asset_balance / 10 ** asset_token.decimals,
                3000
            )

        return total_usd


_async_eth_module = {"eth": (web3.eth.AsyncEth,), "net": (web3.net.AsyncNet,)}
L1_PROVIDER = web3.Web3(
    web3.Web3.AsyncHTTPProvider(src.envs.L1_RPC_URL),
    modules=_async_eth_module,
    middlewares=[],
)
ARBITRUM_PROVIDER = web3.Web3(
    web3.Web3.AsyncHTTPProvider(src.envs.ARBITRUM_RPC_URL),
    modules=_async_eth_module,
    middlewares=[],
)

# black: ignore
L1_ASSETS = [
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC
]

# black: ignore
ARBITRUM_ASSETS = [
    "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC
    "0x1A5B0aaF478bf1FDA7b934c76E7692D722982a6D"
]

w3s = [
    NetworkProvider(
        network="Ethereum mainnet L1",
        network_label=NetworkLabel.L1,
        provider=L1_PROVIDER,
        assets=L1_ASSETS,
        usd_stablecoin_address="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        weth_address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    ),
    NetworkProvider(
        network="Arbitrum One L2",
        network_label=NetworkLabel.ARBITRUM,
        provider=ARBITRUM_PROVIDER,
        assets=ARBITRUM_ASSETS,
        usd_stablecoin_address="0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC
        weth_address="0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
    ),
]
