import pathlib


def _read_abi(filename: str) -> str:
    path = pathlib.Path("abi", f"{filename}.json")
    return path.read_text(encoding="UTF-8")


ERC20 = _read_abi("ERC20")
NonfungiblePositionManager = _read_abi("NonfungiblePositionManager")
UniswapV3Factory = _read_abi("UniswapV3Factory")
UniswapV3Pool = _read_abi("UniswapV3Pool")
