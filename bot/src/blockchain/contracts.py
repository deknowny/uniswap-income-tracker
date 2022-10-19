import abc
import dataclasses
import typing

import web3.contract

import src.blockchain.abi
import src.blockchain.to_address


Cls = typing.TypeVar("Cls")


@dataclasses.dataclass
class _IConnectedContract(abc.ABC):
    w3: web3.Web3
    address: str
    contract: web3.contract.Contract

    @classmethod
    def connect(cls: typing.Type[Cls], w3: web3.Web3, address: str) -> Cls:
        return cls(
            w3=w3,
            address=address,
            contract=w3.eth.contract(
                src.blockchain.to_address.to_address(address),
                abi=cls._get_abi(),
            ),
        )

    @classmethod
    @abc.abstractmethod
    def _get_abi(cls) -> str:
        pass


@dataclasses.dataclass
class _IStaticConnectedContract(_IConnectedContract, abc.ABC):
    @classmethod
    def static_connect(cls: typing.Type[Cls], w3: web3.Web3) -> Cls:
        address = cls._get_address()
        return cls(
            w3=w3, address=address, contract=w3.eth.contract(
                src.blockchain.to_address.to_address(address),
                abi=cls._get_abi(),
            )
        )

    @classmethod
    @abc.abstractmethod
    def _get_address(cls) -> str:
        pass


@dataclasses.dataclass
class NonfungiblePositionManagerContract(_IStaticConnectedContract):
    @classmethod
    def _get_abi(cls) -> str:
        return src.blockchain.abi.NonfungiblePositionManager

    @classmethod
    def _get_address(cls) -> str:
        return "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"


@dataclasses.dataclass
class UniswapV3FactoryContract(_IStaticConnectedContract):
    @classmethod
    def _get_abi(cls) -> str:
        return src.blockchain.abi.UniswapV3Factory

    @classmethod
    def _get_address(cls) -> str:
        return "0x1F98431c8aD98523631AE4a59f267346ea31F984"


@dataclasses.dataclass
class UniswapV3PoolContract(_IConnectedContract):
    @classmethod
    def _get_abi(cls) -> str:
        return src.blockchain.abi.UniswapV3Pool


class ERC20TokenContract(_IConnectedContract):
    @classmethod
    def _get_abi(cls) -> str:
        return src.blockchain.abi.ERC20
