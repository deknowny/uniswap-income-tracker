import dataclasses

import web3.eth
import web3.net

import src.envs


@dataclasses.dataclass
class NetworkProvider:
    network: str
    provider: web3.Web3


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

w3s = [
    NetworkProvider(network="Ethereum mainnet L1", provider=L1_PROVIDER),
    NetworkProvider(network="Arbitrum One L2", provider=ARBITRUM_PROVIDER),
]
