import discord
import discord.ext
from discord.ext import commands
from discord.ext.commands.context import Context
from requests import ReadTimeout
import discord.utils
import json
import os, random

from .pcredive_pvp_api.client import ApiException, PcrClientApi, PcrClientInfo
import datetime
with open('setting.json', 'r', encoding='utf8') as jfile:
	jdata = json.load(jfile)

if os.path.exists("configuration.json"):
    with open("configuration.json", "r", encoding="utf8") as config_file:
        config = json.load(config_file)
else:
    config = {}
    
maintainer_id = jdata.get("Owner_id")
async def check_permission(ctx):
    if (ctx.author.id in maintainer_id) == False:
        await ctx.send("該使用者無法使用這項指令") 
        return False
    return True


class Cog_Extension(commands.Cog):
    """用於Cog繼承基本屬性"""
    def __init__(self, bot):
        self.bot = bot

def hour_min_format(total_seconds):
    days = total_seconds//86400
    hour = (total_seconds%86400)//3600
    minutes = (total_seconds//60) % 60
    seconds = total_seconds % 60
    if days <= 0:
        return str.format("{}時{}分{}秒", hour,minutes,seconds)
    else:
        return str.format("{}天{}時{}分",days,hour,minutes)

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
    

def get_valid_id(ctx:Context):
    dc_id = None
    try:
        arr = ctx.message.content.split(" ")
        arr = [c for c in arr if len(c)>=1]
        if len(arr) == 0:
            return None, None
        if len(arr) >= 2:
            game_id = int(arr[1])
        if len(arr) >= 3:
            dc_id = int(arr[2])
        if game_id < 10_000_000:
            return None, None
    except:
        return None, None
    return game_id, dc_id

async def _re_get_info(ctx:Context, api:PcrClientApi, game_id):
    try:
        res = await api.query_target_user_game_id_async(game_id)
    except ApiException as api_exception:
        await ctx.send(str.format("code={} data={}", api_exception.code, api_exception.message))
    except Exception as err:
        raise err
    return res    

async def get_info(ctx:Context, api:PcrClientApi, game_id):
    if api.is_async_start is False:
        await api.start_async_session()
    try:
        res = await api.query_target_user_game_id_async(game_id)
    except ApiException as api_exception:
        if api_exception.code is None:
            await ctx.send(str.format("code={} data={}", api_exception.code, api_exception.message))
            return
        if type(api_exception.code) is str and \
           len(api_exception.code) >= 1 and \
           api_exception.code[0] != "2":
            await ctx.send(str.format("code={} data={}", api_exception.code, api_exception.message))
            return
        await ctx.send("伺服器需要重新登入, 開始重新登入")
        await api.login_async()
        res = await _re_get_info(ctx, api, game_id)
    except Exception as err:
        raise err
    return res

def generate_embed_result(res:PcrClientInfo, detail:bool=False):
    title_text  = f"[玩家] {res.user_name} @{hour_min_format(res.last_login_idle_seconds)}" 
    title_description = f"`遊戲ID: {res.user_id}`"
    embed = discord.Embed(title=title_text, description=title_description, color=0x28ddb0)
    
    rank_title = f"戰鬥/公主競技場 [{res.pvp1_group}區, {res.pvp3_group}區]"
    rank_text  = f"`{res.pvp1_rank}名 / {res.pvp3_rank}名`"
    embed.add_field(name=rank_title, value=rank_text, inline=False)
    if detail:
        d1_title = f"等級 / 所屬戰隊 / 角色數量 / 全角色戰力"
        d1_text  = f"`{res.user_level}等 / {res.clan_name} / {res.user_character_count} / {res.user_total_power // 10000}萬`"
        embed.add_field(name=d1_title, value=d1_text, inline=False)
        embed.add_field(name="自我簡述", value=f"`{res.user_comment}`", inline=False)
    # embed.add_field(name="分區", value=res.pvp1_group, inline=True)
    # embed.add_field(name = chr(173), value = chr(173))
    # embed.add_field(name="公主競技場排名 (3v3)", value=res.pvp3_rank, inline=True)
    # embed.add_field(name="分區", value=res.pvp3_group, inline=True)
    # embed.add_field(name="閒置時間", value=hour_min_format(res.last_login_idle_seconds), inline=False)
    # embed.add_field(name="上次登入時間", value=str(datetime.datetime.fromtimestamp(res.last_login_time)), inline=False)
    return embed


    


class PcReDiveGameProfile(Cog_Extension):
    def __init__(self, bot):
        super().__init__(bot)
        bot.remove_command('help')
        self.config_dict = config
        self.api = PcrClientApi(configuration_dict=self.config_dict)
    
    @commands.command()
    async def me(self, ctx:Context):
        '''[查詢自己的Id] --- me'''
        await self.query_self(ctx)

    @commands.command("qqme")
    async def qqme(self, ctx:Context):
        '''[查詢自己的細節] --- qq me'''
        await self.query_self(ctx, detail=True)
        
    
    @commands.command()
    async def bind(self, ctx:Context):
        '''[綁定玩家Id] --- bind {自己的遊戲id} {discord id}'''
        game_id, dc_id  = get_valid_id(ctx)
        if game_id is None:
            await ctx.send(str.format("遊戲id格式不正確,格式為 `{}`", format_doc(self.bind.short_doc)))
            return
        
        if dc_id is None:
            self.api.bind_user_id(ctx.author.id, game_id)
        else:
            if await check_permission(ctx) == False:
                return
            else:
                self.api.bind_user_id(dc_id, game_id)
            
        await ctx.send("綁定成功")
    
    @commands.command("q")
    async def _q(self, ctx:Context):
        '''[查詢玩家Id] --- q {遊戲id}'''
        await self._query(ctx)

    @commands.command("qq")
    async def _qq(self, ctx:Context):
        '''[查詢玩家細節] --- qq {遊戲id}'''
        arr = ctx.message.content.split(" ")
        arr = [c for c in arr if len(c)>=1]
        if len(arr) >= 2 and arr[1] == "me":
            await self.query_self(ctx, detail=True)
            return
        await self._query(ctx, detail=True)
    
    async def query_self(self, ctx:Context, detail:bool=False):
        game_id = self.api.binding_id_dict.get(str(ctx.author.id), None)
        if game_id is None:
            await ctx.send("此discord帳號尚未綁定遊戲id")
            return
        res = await get_info(ctx, self.api, game_id)
        if res is not None:
            await ctx.send(embed=generate_embed_result(res, detail))

    async def _query(self, ctx:Context, detail:bool=False):
        '''[查詢玩家Id] --- query {遊戲id}'''
        if ctx.message.content.strip() == "":
            await self.query_self(ctx)
            return
        game_id, _ = get_valid_id(ctx)
        if game_id is None:
            await ctx.send(str.format("遊戲id格式不正確,格式為 `{}`", format_doc(self.query.short_doc)))
            return
        
        res = await get_info(ctx, self.api, game_id)
        if res is not None:
            await ctx.send(embed=generate_embed_result(res, detail))
        
def setup(bot):
    bot.add_cog(PcReDiveGameProfile(bot))