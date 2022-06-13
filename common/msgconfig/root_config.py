import pathlib
import os
from .message import MessageSetting

def get_all_files(target_path):
    path_list = [os.path.join(target_path, f) for f in os.listdir(target_path) ]
    path_list = [ f for f in path_list if os.path.isfile(f) ]
    return path_list
    

class RootConfig:
    def __init__(self, config_topic:str, root_path:str=".config"):
        target_path = pathlib.Path(root_path).joinpath(config_topic)
        os.makedirs(str(target_path), exist_ok=True)
        self.file_list = set(get_all_files(target_path))
        
    #TODO: read all configs
    
    def dump_setting(self, setting:MessageSetting):
        pass
        
        