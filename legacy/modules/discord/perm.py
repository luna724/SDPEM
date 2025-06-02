from discord.ext.commands import Context, Cog
from discord import Interaction
from functools import wraps

from modules.discord.jsk import Jishaku


def PermissionManager():
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if isinstance(args[0], Context) or isinstance(args[0], Interaction):
                ctx = args[0]
            elif isinstance(args[0], Cog):
                ctx = args[1]
            else:
                raise RuntimeError("PermissionLevel decorator are must be parent of bot commands.")
            if not isinstance(ctx, Context) and not isinstance(ctx, Interaction):
                raise RuntimeError("ctx not found in PermissionLevel!")

            if isinstance(ctx, Interaction):
                user_id = ctx.user.id
            else:
                user_id = ctx.author.id

            if user_id in Jishaku.token_file().get("allowlist", []):
                return await func(*args, **kwargs)
            if isinstance(ctx, Interaction):
                await ctx.followup.send(
                    "You don't have permission to use this command.", ephemeral=True
                )
        return wrapper
    return decorator