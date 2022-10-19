import vkquick as vq

from src.command.track import track

pkg = vq.Package()


@pkg.command("ping", "пинг")
async def ping(ctx: vq.NewMessage):
    kb = vq.Keyboard(
        vq.Button.text("Tracker").primary().on_click(track), one_time=False
    )
    await ctx.reply("Check out keyboard!", keyboard=kb)
