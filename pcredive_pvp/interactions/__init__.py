import asyncio

class BotModel:
    def __init__(self, bot):
        self.bot = bot
        self.guilds = []
                
def init_asyncio():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
        