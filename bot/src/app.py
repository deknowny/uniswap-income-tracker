import vkquick as vq

from src.command import track, ping
from src.users import USERS

filter_users = vq.filters.Dynamic(lambda ctx: str(ctx.msg.from_id) in USERS)
app = vq.App(filter=filter_users)
app.add_package(track.pkg)
app.add_package(ping.pkg)
