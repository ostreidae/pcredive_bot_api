import asyncio
import interactions
from . import BotModel
import atexit




class BotModelProcessor:
    def __init__(self, token:str):
        self.bot = interactions.Client(token)
        self.model    = BotModel(self.bot)
        self.commands = BotCommands(self.model)
    
    def init_model(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.get_guilds())
        #loop.run_until_complete(self.remove_all_commands())
        self.commands.bind_bot_commands()
    
    def start(self):
        #atexit.register(self.__clean_up__)
        self.bot.start()
        
    def __clean_up__(self):
        #loop = asyncio.get_event_loop()
        #loop.run_until_complete(self.remove_all_commands())
        print("commands are removed")
    
    async def get_guilds(self):
        guilds = await self.bot._http.get_self_guilds()
        self.model.guilds = [ 
            int(ret.get('id', None)) for ret in guilds 
                if ret.get('id', None) is not None]
        
    async def remove_all_commands(self):
        bot = self.bot
        for guild in self.model.guilds:
            commands = await bot._http.get_application_commands(
                application_id=bot.me.id, guild_id=guild)
            if type(commands) is list:
                for cmd in commands:
                    cmd_id = cmd.get('id', None)
                    app_id = cmd.get('application_id', None)
                    guild_id = cmd.get('guild_id', None)
                    await bot._http.delete_application_command(app_id, cmd_id, guild_id)
            print(commands)
        

class BotCommands:    
    def __init__(self, model:BotModel):
        self.model    = model
        self.bot : interactions.Client = model.bot 
        
    async def on_ready(self):
        print(">> Interaction Bot is online <<")

    async def main_command(self, ctx, response:str):
        await ctx.send(str.format("Hi there! {0}",response))
  
    def bind_bot_commands(self):
        bot = self.bot
        guilds = self.model.guilds
        
        main_dec = bot.command(name="main", description="主控面板", scope=guilds, options=[interactions.Option(
                    name="輸入文字",
                    description="底下重複一樣的內容",
                    type=interactions.OptionType.STRING,
                    required=True,
                )])
        main_dec(self.main_command)
        
        bot.event(self.on_ready)