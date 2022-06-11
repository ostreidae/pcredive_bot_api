import json
import time
import os
import threading
import traceback
import sys

import discord
from discord.ext import commands

import json
import random, asyncio

class Cog_Extension(commands.Cog):
    """用於Cog繼承基本屬性"""
    def __init__(self, bot):
        self.bot = bot

def watch_parent_program_id(parent_pid):
    if os.name != 'nt':
        return
    from ctypes import WinDLL, WinError
    from ctypes.wintypes import DWORD, BOOL, HANDLE
    SYNCHRONIZE = 0x00100000
    kernel32 = WinDLL("kernel32.dll")
    kernel32.OpenProcess.argtypes = (DWORD, BOOL, DWORD)
    kernel32.OpenProcess.restype = HANDLE
    parent_handle = kernel32.OpenProcess(SYNCHRONIZE, False, parent_pid)
    # Block until parent exits
    print(str.format("start to watch parent process state, child pid is {}", os.getpid()))
    try:
        os.waitpid(parent_handle, 0)
    except:
        print(traceback.format_exc())
        pass
    print("detect parent is done, exit.")
    os._exit(0)

def get_int(arg:str):
    try:
        return int(arg)
    except:
        return -1


with open('setting.json', 'r', encoding='utf8') as jfile:
    jdata : dict = json.load(jfile)
    

from pcredive_pvp.interactions import init_asyncio


def init_interaction_py():
    token = jdata.get("TOKEN", "")
    
    init_asyncio()
    from pcredive_pvp.interactions.main import BotModelProcessor
    bot_processor = BotModelProcessor(token=token)
    bot_processor.init_model()
    bot_processor.start()
        
    
def init_interactions_py_backgroud_thread():
    thread = threading.Thread(target=init_interaction_py, daemon=True)
    thread.start()
    return thread
    

if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) > 1:
        parent_id = get_int(sys.argv[1])
        if parent_id != -1:
            watch_thread = threading.Thread(target=watch_parent_program_id, args=(parent_id,))
            watch_thread.start()
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix= jdata['Prefix'], owner_ids= jdata['Owner_id'])
    @bot.event
    async def on_ready():
        print(">> Subprocess Bot is online <<")
    #dir_path         = os.path.dirname(__file__)
    #target_file_path = os.path.join(dir_path, "game_profile.py")
    thread = init_interactions_py_backgroud_thread()
    #thread.join()
    bot.load_extension("pcredive_pvp.cmds.game_profile")
    bot.run(jdata['TOKEN'])