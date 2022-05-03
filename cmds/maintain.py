import threading
import discord
from discord.ext import commands
from discord.ext.commands.context import Context
from requests import ReadTimeout
import discord.utils
from core.classes import Cog_Extension
from core import check
import json
import os, random

import datetime
import sys
from discord.ext.commands.context import Context
import subprocess
from discord.ext.commands.errors import CommandNotFound
from core.errors import Errors
    
url = "https://raw.githubusercontent.com/ostreidae/pcredive_bot_api/main/version"
download_url = "https://github.com/ostreidae/pcredive_bot_api/archive/refs/heads/main.zip"
maintainer_id = [764383189439348777, 971077292384219226]

with open('setting.json', 'r', encoding='utf8') as jfile:
	jdata = json.load(jfile)
 
with open('version', 'r', encoding='utf8') as version_file:
	version = version_file.read()

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
    
    @commands.command()
    async def update(self, ctx:Context):
        if (ctx.author.id in maintainer_id) == False:
            await ctx.send("該使用者無法使用這項指令") 
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
        prev_id = self.restart_process()
        if prev_id is not None:
            await ctx.send(str.format("程序 {} 已終止, 重啟程序 {}", prev_id, self.process.pid))
        else:
            await ctx.send(str.format("重啟程序 {}", self.process.pid))
    
    @commands.command()
    async def restart(self, ctx:Context):
        if(ctx.author.id in maintainer_id):
            prev_id = self.restart_process()
            if prev_id is not None:
                await ctx.send(str.format("程序 {} 已終止, 重啟程序 {}", prev_id, self.process.pid))
            else:
                await ctx.send(str.format("重啟程序 {}", self.process.pid))
            #await send_another(ctx.channel)
        else:
            await ctx.send("該使用者無法使用這項指令")
        #sys.exit(0)


def setup(bot):
    setattr(Errors, 'None_error', process_error)
    bot.add_cog(BackendMaintain(bot))
    