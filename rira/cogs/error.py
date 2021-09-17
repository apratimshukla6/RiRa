import discord
import sys
import traceback
import logging
from discord.ext import commands


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.bot.add_listener(self.on_command_error, "on_command_error")
        
    def create_embed(self, description, title="RiRa", footer=f"RiRa v0.1", thumbnail="https://i.imgur.com/n1guxrV.png"):
        embed = discord.Embed(title=title, description=description, color=discord.Color.red())
        embed.set_thumbnail(url=thumbnail)
        embed.set_footer(text=footer, icon_url=thumbnail)

        return embed

    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, "on_error"):
            return

        error = getattr(error, "original", error)

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.CommandError):
            embed = self.create_embed(f"Error executing command `{ctx.command.name}`: {str(error)}")
            return await ctx.send(embed=embed)

        embed = self.create_embed("An unexpected error occurred while running that command.")
        await ctx.send(embed=embed)
        logging.warn("Ignoring exception in command {}:".format(ctx.command))
        logging.warn("\n" + "".join(traceback.format_exception(type(error), error, error.__traceback__)))
