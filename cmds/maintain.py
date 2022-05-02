import discord
from discord.ext import commands
from discord.ext.commands.context import Context
from requests import ReadTimeout
import discord.utils
from core.classes import Cog_Extension
from core import check
import json
import os, random

from cmds.pcredive_pvp.client import ApiException, PcrClientApi, PcrClientInfo
import datetime


class Maintain(Cog_Extension):
    def __init__(self) -> None:
        super().__init__()

def setup(bot):
    pass
	#bot.add_cog(PcReDiveGameProfile(bot))