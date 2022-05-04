import threading
import discord
from discord.ext import commands
from discord.ext.commands.context import Context
from requests import ReadTimeout
import discord.utils
import requests
from core.classes import Cog_Extension
from core import check
import json
import os, io

import datetime
import sys
from discord.ext.commands.context import Context
import subprocess
from discord.ext.commands.errors import CommandNotFound
from core.errors import Errors
help_message = \
"""
#【競技場功能】
  [綁定Discord Id]  {0}bind  {{自己的遊戲id}}
  [查詢自己的 Id]   {0}me 
  [查詢玩家Id]      {0}query {{遊戲id}}
  
#【維護功能】
  [從github更新版本]  {0}update
  [重新啟動]          {0}restart
  [暫停查詢功能]      {0}stop
  [下載檔案]          {0}download {{檔名路徑}} {{URL位址}}
  [刪除檔案]          {0}delete {{檔名路徑}}
  [查詢程序列表]      {0}list-child-process
  [停止所有子程序]    {0}stop-child-process
  [印出目前設定檔內容]  {0}dump-config
  [開發日誌]           {0}about
"""
with open('setting.json', 'r', encoding='utf8') as jfile:
	jdata : dict = json.load(jfile)
 
with open('version', 'r', encoding='utf8') as version_file:
	version = version_file.read()

prefix = jdata.get("Prefix", "")
if type(prefix) is list:
    prefix = prefix[0] if len(prefix) >=1 else ""
 
help_message = str.format(help_message, prefix)
url = "https://raw.githubusercontent.com/ostreidae/pcredive_bot_api/main/version"
download_url = "https://github.com/ostreidae/pcredive_bot_api/archive/refs/heads/main.zip"
maintainer_id = jdata.get("Owner_id")


async def send_another(channel):
    await channel.send("Hello World")
    

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

class BackendMaintain(Cog_Extension):
    def __init__(self, bot):
        super().__init__(bot)
        bot.remove_command('help')
        self.lock = threading.Lock()
        self.process = None
        self.restart_process()
        
    def restart_process(self):
        with self.lock:
            if self.process is None:
                self.process = subprocess.Popen(str.format('python ./cmds/pcredive_pvp/run.py {}', os.getpid()))
            elif self.process.poll() is None:
                prev_id = self.process.pid
                self.process.kill()
                self.process = subprocess.Popen(str.format('python ./cmds/pcredive_pvp/run.py {}', os.getpid()))
                return prev_id
            else:
                self.process = subprocess.Popen(str.format('python ./cmds/pcredive_pvp/run.py {}', os.getpid()))
                
    async def check_permission(self, ctx):
        if (ctx.author.id in maintainer_id) == False:
            await ctx.send("該使用者無法使用這項指令") 
            return False
        return True
    
    async def reload(self, ctx):
        extension = "maintain"
        pid = self.stop_process()
        self.bot.reload_extension(f'cmds.{extension}')
        if pid is None:
            await ctx.send(f'維護程式重新加載完成')
        else:
            await ctx.send(str.format('維護套件重新加載完成, 子程序 {} 已終止', pid))
            
    def stop_process(self):
        with self.lock:
            if self.process is not None:
                if self.process.poll() is None:
                    pid = self.process.pid
                    self.process.kill()
                    self.process = None
                    return pid
                
    @commands.command()
    async def about(self, ctx:Context):
        if os.path.exists("version"):
            with open("version", "r", encoding="utf8") as version_file:
                version = version_file.read()
                await ctx.send(str.format("```\n版本 {} \n```", version))
                
    @commands.command()
    async def help(self, context):
        if os.path.exists("version"):
            with open("version", "r", encoding="utf8") as version_file:
                version = version_file.read()
                version = version.split("\n")[0]
        await context.send( str.format("```版本 {}\n", version) + help_message + "\n```" )
                
    @commands.command("dump-config")
    async def dump_config(self, ctx:Context):
        if os.path.exists("configuration.json"):
            with open("configuration.json", "r", encoding="utf8") as config_file:
                await ctx.send(config_file.read())
                
    @commands.command("stop-child-process")
    async def stop_child_process(self, ctx:Context):
        if await self.check_permission(ctx) == False:
            return
        import psutil
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        pid_list = [str(ch.pid) for ch in children]
        for ch in children:
            ch.kill()
        await ctx.send(str.format("子程序列表: {} 已經停止", ", ".join(pid_list)))
    
    @commands.command("list-child-process")
    async def list_child_process(self, ctx:Context):
        if await self.check_permission(ctx) == False:
            return
        import psutil
        current_process = psutil.Process()
        children = current_process.children(recursive=True)
        pid_list = [str(ch.pid) for ch in children]
        await ctx.send(str.format("子程序列表: {}", ", ".join(pid_list)))
        
    
    @commands.command()
    async def delete(self, ctx:Context):
        if await self.check_permission(ctx) == False:
            return
        message : str = ctx.message.content
        arr = message.split(" ", 2)
        if len(arr) <= 1:
            await ctx.send("格式錯誤")
            return
        os.remove(arr[1])
        await ctx.send(str.format("檔案 {} 已刪除", arr[1]))
        
    @commands.command()
    async def download(self, ctx:Context):
        if await self.check_permission(ctx) == False:
            return
        message : str = ctx.message.content
        arr = message.split(" ", 3)
        if len(arr) <= 2:
            await ctx.send("格式錯誤")
            return
        file_name = arr[1]
        url = arr[2]
        resp = requests.get(url)
        with open(file_name, "wb") as f:
            f.write(resp.content)
        await ctx.send(str.format("檔案 {} 已從 {} 下載完成", file_name, url))
    
    @commands.command()
    async def stop(self, ctx:Context):
        if await self.check_permission(ctx) == False:
            return
        pid = self.stop_process()
        if pid is not None:
            await ctx.send(str.format("程序 {} 終止", pid))
        else:
            await ctx.send("目前無運行程序")
            
    @commands.command()
    async def update(self, ctx:Context):
        if await self.check_permission(ctx) == False:
            return
        import requests, zipfile, io, shutil
        r = requests.get(download_url)
        archive = zipfile.ZipFile(io.BytesIO(r.content))
        shutil.rmtree('/cmds/pcredive_pvp', ignore_errors=True)
        for file in archive.namelist():
            if file.endswith('/'):
                continue
            if file.startswith('pcredive_bot_api-main/'):
                source_path = file
                target_path = file.replace('pcredive_bot_api-main/', '')
                if target_path == '':
                    continue
                source = archive.open(source_path)
                target = open(os.path.join(os.getcwd(), target_path), "wb")
                with source, target:
                    shutil.copyfileobj(source, target)
        await ctx.send("更新完成, 重啟程序")
        await self.reload(ctx)

    @commands.command()
    async def restart(self, ctx:Context):
        if await self.check_permission(ctx) == False:
            return
        await self.reload(ctx)


def setup(bot):
    setattr(Errors, 'None_error', process_error)
    bot.add_cog(BackendMaintain(bot))
    