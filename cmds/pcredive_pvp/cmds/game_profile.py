import discord
from discord.ext import commands
from discord.ext.commands.context import Context
from requests import ReadTimeout
import discord.utils
import json
import os, random

from .api.client import ApiException, PcrClientApi, PcrClientInfo
import datetime

with open('setting.json', 'r', encoding='utf8') as jfile:
	jdata = json.load(jfile)

if os.path.exists("configuration.json"):
    with open("configuration.json", "r", encoding="utf8") as config_file:
        config = json.load(config_file)
else:
    config = {}

class Cog_Extension(commands.Cog):
    """用於Cog繼承基本屬性"""
    def __init__(self, bot):
        self.bot = bot

def hour_min_format(total_seconds):
    hour = total_seconds//3600
    minutes = (total_seconds//60) % 60
    seconds = total_seconds % 60
    return str.format("{}時{}分{}秒", hour,minutes,seconds)

def format_doc(doc:str):
    if type(doc) is not str:
        return ""
    arr = doc.split("---")
    if len(arr) <= 1:
        return doc
    else:
        return jdata.get("Prefix","")[0] + arr[1].strip()

def is_matched_restrict_role(author:Context.author, match_role="兔兔帝國"):
    for role in author.roles:
        if role.name == match_role:
            return True
    return False

def parse_command_after(message:str, command_name:str):
    if type(message) is not str:
        return ""
    arr = message.split(" ", 2)
    if len(arr) <= 1:
        return ""
    else:
        return arr[1]
    """
    prefix = jdata.get("Prefix","")[0]
    start_pos = len(prefix) + len(command_name)
    if len(message) <= start_pos:
        return ""
    return message[start_pos:].lstrip()
    """
    


async def check_rol_valid(ctx:Context, match_role="兔兔帝國"):
    res = is_matched_restrict_role(ctx.author, match_role)
    if res == True:
        return res
    await ctx.send(str.format("暫時不開放此身份組使用"))
    return False
    

async def get_valid_id(ctx:Context, message, doc=""):
    try:
        target_id = int(message)
        if target_id < 10_000_000:
            await ctx.send(str.format("遊戲id格式不正確,格式為 `{}`", format_doc(doc)))
            return
    except:
        await ctx.send(str.format("遊戲id格式不正確,格式為 `{}`", format_doc(doc)))
        return
    return target_id

async def get_info(ctx:Context, api:PcrClientApi, game_id):
    try:
        res = api.query_target_user_game_id(game_id)
    except ApiException as api_exception:
        await ctx.send(str.format("code={} data={}", api_exception.code, api_exception.message))
        return
    except Exception as err:
        raise err
    return res

def generate_embed_result(res:PcrClientInfo):
    embed = discord.Embed(title=str.format("[玩家] {}", res.user_name), description=res.user_id, color=0x28ddb0)
    embed.add_field(name="戰鬥競技場排名 (1v1)", value=res.pvp1_rank, inline=True)
    embed.add_field(name="分區", value=res.pvp1_group, inline=True)
    embed.add_field(name = chr(173), value = chr(173))
    embed.add_field(name="公主競技場排名 (3v3)", value=res.pvp3_rank, inline=True)
    embed.add_field(name="分區", value=res.pvp3_group, inline=True)
    embed.add_field(name="閒置時間", value=hour_min_format(res.last_login_idle_seconds), inline=False)
    embed.add_field(name="上次登入時間", value=str(datetime.datetime.fromtimestamp(res.last_login_time)), inline=False)
    return embed

class PcReDiveGameProfile(Cog_Extension):
    def __init__(self, bot):
        super().__init__(bot)
        self.config_dict = config
        self.api = PcrClientApi(configuration_dict=self.config_dict)
    
    @commands.command()
    async def me(self, ctx:Context):
        '''[查詢自己的Id] --- me'''
        if (await check_rol_valid(ctx, match_role="兔兔帝國")) == False:
            return
        game_id = self.api.binding_id_dict.get(str(ctx.author.id), None)
        if game_id is None:
            await ctx.send("此discord帳號尚未綁定遊戲id")
            return
        res = await get_info(ctx, self.api, game_id)
        if res is not None:
            await ctx.send(embed=generate_embed_result(res))
        
    
    @commands.command()
    async def bind(self, ctx:Context):
        '''[綁定玩家Id] --- bind {自己的遊戲id}'''
        message = parse_command_after(ctx.message.content, "bind")
        if (await check_rol_valid(ctx, match_role="兔兔帝國")) == False:
            return
        game_id  = await get_valid_id(ctx, message, doc=self.bind.short_doc)
        if game_id is None:
            return
        self.api.bind_user_id(ctx.author.id, game_id)
        await ctx.send("綁定成功")
        
    @commands.command()
    async def query(self, ctx:Context):
        '''[查詢玩家Id] --- query {遊戲id}'''
        message = parse_command_after(ctx.message.content, "query")
        if (await check_rol_valid(ctx, match_role="兔兔帝國")) == False:
            return
        game_id = await get_valid_id(ctx, message, doc=self.bind.short_doc)
        if game_id is None:
            return
        
        res = await get_info(ctx, self.api, game_id)
        if res is not None:
            await ctx.send(embed=generate_embed_result(res))
        
def setup(bot):
    bot.add_cog(PcReDiveGameProfile(bot))