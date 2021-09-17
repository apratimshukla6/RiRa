import discord
import logging
import sys
from discord.ext import commands
from .cogs import music, error
from . import config

cfg = config.load_config()

bot = commands.Bot(command_prefix=cfg["prefix"], activity=discord.Activity(type=discord.ActivityType.listening, name="!help ❤️"), help_command=None)

@bot.event
async def on_ready():
    logging.info(f"{bot.user.name} {cfg['version']}")

COGS = [music.Music, error.CommandErrorHandler]

def add_cogs(bot):
    for cog in COGS:
        bot.add_cog(cog(bot, cfg)) 

def run():
    add_cogs(bot)
    if cfg["token"] == "":
        raise ValueError("No token has been provided.")
        sys.exit(1)
    bot.run(cfg["token"])
