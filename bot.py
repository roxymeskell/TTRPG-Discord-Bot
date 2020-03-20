# bot.py
import os
import traceback
import sys
import time

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogfactory import GroupCog, make_cog
from colors import random_color
from help import MyHelpCommand

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!', help_command=MyHelpCommand())
bot.load_extension('base')
bot.load_extension('util')

bot.run(TOKEN)
