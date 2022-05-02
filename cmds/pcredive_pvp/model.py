import json
from typing import Any, Union

class DiscordUserState:
    def __init__(self, discord_id, subscriptions):
        self.discord_id = discord_id
        self.subscriptions = set(subscriptions)
        self.last_query = 0 #limitation for continuous query
        
    
class GlobalPreference:
    def __init__(self):
        pass

class UserPreference:
    
    def __init__(self, user_list : list):
        self.server_user_dict = dict()
        
        for user in user_list:
            user : dict = user
            user_id = user.get('discord_id', None)
            subscriptions = user.get('subscriptions', [])
            if user_id is None:
                continue
            self.server_user_dict[user_id] = DiscordUserState(user_id, subscriptions)
    
    def get_user(self, user_discord_id) -> DiscordUserState:
        return self.server_user_dict.get(user_discord_id, None)
      
    def add_user(self, user_discord_id):
        if type(user_discord_id) is not int:
            return
        self.server_user_dict[user_discord_id] = DiscordUserState(user_discord_id, [])
        
    def subscribe(self, user_discord_id, target_player_id):
        user = self.get_user(user_discord_id)
        if user is None:
            return
        if type(target_player_id) is not int:
            return
        user.subscriptions.add(target_player_id)
        self.dump_state()
        
    def dump_state(self):
        pass
    
    @staticmethod
    def from_json_str(json_str : str):
        return UserPreference(json.loads(json_str))
    
    @staticmethod
    def from_json_file(json_file : Union[str, Any]):
        if type(json_file) is not str:
            return UserPreference.from_json_str(json_file.read())
        
        with open(json_file, 'r') as f:
            return UserPreference.from_json_str(f.read())
    

        
        