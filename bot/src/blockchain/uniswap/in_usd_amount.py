import traceback

import web3

from src.blockchain.contracts import UniswapV3FactoryContract, UniswapV3PoolContract
from src.blockchain.erc20_token import ERC20Token
from src.blockchain.providers import ARBITRUM_PROVIDER, L1_PROVIDER

# USDC
USD_STABLECOIN_CONTRACT_ADDRESS = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"


async def calc_amount_in_usd(w3: web3.Web3, token_address: str, amount: float, fee: int) -> float:
    # Fetch tokens' info
    erc20_token0 = await ERC20Token.fetch(w3, token_address)
    print(str(erc20_token0))
    erc20_token1 = await ERC20Token.fetch(ARBITRUM_PROVIDER, USD_STABLECOIN_CONTRACT_ADDRESS)

    # Fetch liquidity pool for calculating
    factory = UniswapV3FactoryContract.static_connect(w3)
    pool_address = await factory.contract.functions.getPool(
        token_address, USD_STABLECOIN_CONTRACT_ADDRESS, fee
    ).call()
    pool = UniswapV3PoolContract.connect(w3, pool_address)

    sqrt_price_x96 = (await pool.contract.functions.slot0().call())[0]
    price0 = (
            sqrt_price_x96 ** 2
            * (10 ** erc20_token0.decimals / 10 ** erc20_token1.decimals)
            / 2 ** 192
    )
    return price0 * amount
