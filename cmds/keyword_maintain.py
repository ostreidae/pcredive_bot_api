import asyncio
import threading
import time
from typing import List
from discord.ext import commands
import discord
from discord.ext.commands.errors import CommandNotFound
from cmds.keyword.model import KeyWordModel
from core.errors import Errors
from .keyword.maintain import KeyWordController
from core.classes import Cog_Extension
import json
from discord.ext.commands.context import Context

with open('setting.json', 'r', encoding='utf8') as jfile:
	jdata : dict = json.load(jfile)
maintainer_id = jdata.get("Owner_id") 
prefix = jdata.get("Prefix", "")
if type(prefix) is list:
    prefix = prefix[0] if len(prefix) >=1 else ""
    
help_message = \
"""
[幫助]                  {0}keyword help
[檢視關鍵字集合]        {0}keyword show {{關鍵字}}
[新增關鍵字至集合]      {0}keyword add {{關鍵字}} {{內容}}
[刪除關鍵字之一  ]      {0}keyword del {{關鍵字}}
[新增至集合並且tag自己] {0}keyword add-tag-me {{關鍵字}} {{內容}}
[新增至集合並且tag別人] {0}keyword add-tag {{discord-id}} {{關鍵字}} {{內容}}
"""

admin_help_message = \
"""
#【維護功能】
    [備份檔案] {0}keyword backup
"""
admin_help_message = str.format(admin_help_message, prefix)
help_message = str.format(help_message, prefix)
 
async def process_error(s, ctx, error):
    if type(error) is CommandNotFound:
        pass
        #command = error.args[0].replace("Command ", "").replace(" is not found", "").replace("\"","")
        #if command in ["me", "bind", "query"]:
        #    pass
        #else:
            #await Errors.default_error(s, ctx, error)
    else:
        await Errors.default_error(s, ctx, error)


def as_int(s:str):
    try:
        return int(s)
    except:
        return -1


class KeywordMaintain(Cog_Extension):
    def __init__(self, bot) -> None:
        super().__init__(bot)
        self.bot : discord.Client = self.bot
        self.controller = KeyWordController(maintainer_ids=maintainer_id)
        self.lock = asyncio.Lock()
        self.user_waiting_dict = dict()
        bot.event(self.on_message)
    
    def _show_all_content(self, keyword):
        res : List[KeyWordModel] = self.controller.get_keyword_alllist(keyword)
        if res is None or (type(res) is list and len(res) == 0):
            return ""
        converter = lambda x : "[@other]" if x > 0 else ""
        
        content = "\n".join([
           f"[{idx}]{converter(f.tag_user_id)} {f.content}" for idx, f in enumerate(res)
        ])
        return f"```\n{content}\n```"
    
    async def _get_help_message(self, ctx:Context):
        message : discord.Message = ctx.message
        user_id : int = message.author.id
        if user_id in maintainer_id:
            await ctx.send(f"```{help_message}\n{admin_help_message}```") 
        else:
            await ctx.send(f"```{help_message}```") 
            
        
    
    def generate_del_waiting_request(self, user_id, channel_id, keyword):
        t = time.time()
        self.user_waiting_dict[(user_id, channel_id)] = (user_id, channel_id, keyword, t)
        
    async def on_message(self, message:discord.Message):
        ret = await self._on_message(message)
        if ret is None:
            await self.bot.process_commands(message)
    
    async def _on_message(self, message:discord.Message):
        content : str = message.content
        user_id    : int = message.author.id
        channel_id : int = message.channel.id
        req = self.user_waiting_dict.get((user_id, channel_id), None)
        if req is None:
            if len(content) > self.controller.max_keyword_length:
                return
            res : KeyWordModel = self.controller.get_keyword(content)
            if res is None or res == "":
                return
            
            content = res.content.split('\n')
            if res.tag_user_id > 0:
                await message.channel.send(f"<@{res.tag_user_id}>\n{content[0]}")
            else:
                await message.channel.send(res.content[0])
            if len(content) > 1:
                for c in content[1:]:
                    if len(c) > 0:
                        await message.channel.send(c)
            return 0
            
        async with self.lock:
            user_id, channel_id, keyword, t = self.user_waiting_dict.pop((user_id, channel_id))
            if time.time() - t > 60:
                return 0
            if len(content) <= 3:
                index = as_int(content)
                if index < 0:
                    await message.channel.send("索引格式錯誤")
                res = self.controller.del_keyword(keyword, index, user_id)
                if res == "" or res is None:
                    await message.channel.send(f"關鍵字 {keyword} 集合已刪除索引 {index}")
                else:
                    await message.channel.send(res)
        return 0
        
       
    @commands.command()
    async def keyword(self, ctx:Context):
        async with self.lock:
            message : discord.Message = ctx.message
            message_content : str = message.content
            user_id : int = message.author.id
            channel_id : int = message.channel.id
            
            arr = message_content.split(' ')
            if len(arr) <= 1:
                await self._get_help_message(ctx)
                return
            
            command = arr[1]
            if command == "backup":
                if user_id in maintainer_id:
                    self.controller.backup_dump()
                    await ctx.send("備份完成")
            if command == "add" or command == "add-tag-me":
                if len(arr) <= 3:
                    await self._get_help_message(ctx)
                    return
                keyword = arr[2]
                content = " ".join(arr[3:])
                if command == "add-tag-me":
                    res = self.controller.add_new_keyword(keyword, content, user_id, user_id)
                else:
                    res = self.controller.add_new_keyword(keyword, content, user_id)
                if res != "":
                    await ctx.send(res)
                    return
                else:
                    await ctx.send(f"關鍵字 {keyword} 集合擴增成功")
                
            elif command == "del" or command == "show":
                if len(arr) <= 2:
                    await self._get_help_message(ctx)
                    return
                keyword = arr[2]
                target  = self._show_all_content(keyword)
                if target is None or target == "":
                    await ctx.send("查無關鍵字")
                else:
                    if command == "del":
                        await ctx.send(f"請在60秒內選擇其中一個索引:\n{target}")
                        self.generate_del_waiting_request(user_id, channel_id, keyword)
                    else:
                        await ctx.send(target)
                    
                    
            elif command == "add-tag":
                if len(arr) < 4:
                    await self._get_help_message(ctx)
                    return
                tag_user_id = as_int(arr[2]) 
                keyword = arr[3]
                content = " ".join(arr[4:])
                if tag_user_id == -1:
                    await ctx.send("discord id 不正確")
                    return
                res = self.controller.add_new_keyword(keyword, content, user_id, tag_user_id)
                if res != "":
                    await ctx.send(res)
                else:
                    await ctx.send(f"關鍵字 {keyword}  集合擴增成功")
        
    
def setup(bot : commands.Bot):
    setattr(Errors, 'None_error', process_error)
    bot.add_cog(KeywordMaintain(bot))