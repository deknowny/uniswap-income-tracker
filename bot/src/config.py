import starlette.config
import starlette.datastructures


config = starlette.Config()

ALLOWED_USERNAMES = config(
    "ALLOWED_USERNAMES", cast=starlette.datastructures.CommaSeparatedStrings
)
