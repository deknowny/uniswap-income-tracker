import starlette.config


config = starlette.config.Config()

VK_BOT_GROUP_TOKEN = config("VK_BOT_GROUP_TOKEN", cast=str)
L1_RPC_URL = config("L1_RPC_URL", cast=str)
ARBITRUM_RPC_URL = config("ARBITRUM_RPC_URL", cast=str)
