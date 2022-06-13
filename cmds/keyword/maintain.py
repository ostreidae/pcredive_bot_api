from collections import defaultdict
import os
from textwrap import indent
import common.cattrs as cattrs
import json
from typing import DefaultDict, Set
from .model import KeyWordModel, KeyWordSetting

import random
def read_file(path_name):
    with open(path_name, "r") as f:
        return f.read()

def to_lower_keys(dic):
    keys = [ k.lower() for k in dic.keys() ]
    return dict(zip(keys, list(dic.values())))

class KeyWordController:
    def __init__(self, config_file_path="keywordconfig.json",
                     prefix_filter=set("!@#$%^&*()[]\\/?><\"';:{}|-_=+~`"),
                     maintainer_ids:Set[int]=set()):
        self.maintainer_ids = set() if maintainer_ids is None else maintainer_ids
        self.prefix_filter = prefix_filter
        self.path = config_file_path
        if not os.path.exists(config_file_path):
            self.setting = KeyWordSetting()
        else:
            content = read_file(config_file_path)
            self.setting = cattrs.structure(json.loads(content), KeyWordSetting)
            self.setting.key_mapping_dict = to_lower_keys(self.setting.key_mapping_dict)
            self.setting.key_mapping_dict = defaultdict(list, self.setting.key_mapping_dict)
                
        self.user_count = self._count_user()
    
    @property
    def max_keyword_length(self):
        return self.setting.max_keyword_length
    
    def _dump(self):
        try:
            with open(self.path, "w") as f:
                f.write(json.dumps(cattrs.unstructure(self.setting), indent=4))
        except:
            pass
        
    def backup_dump(self):
        with open(self.path+".bak", "w") as f:
            f.write(json.dumps(cattrs.unstructure(self.setting), indent=4))
        with open(self.path, "w") as f:
            f.write(json.dumps(cattrs.unstructure(self.setting), indent=4))
            
    
    def _count_user(self) -> DefaultDict[int, int]:
        count_dict = defaultdict(int)
        for lst in self.setting.key_mapping_dict.values():
            for model in lst:
                if model.set_user_id > 0:
                    count_dict[model.set_user_id] += 1
        return count_dict
    
    def get_keyword_alllist(self, keyword:str):
        keyword = keyword.lower()
        return self.setting.key_mapping_dict.get(keyword)
    
    def get_keyword(self, keyword:str, use_random=True, fetch_index=-1):
        keyword = keyword.lower()
        res = self.setting.key_mapping_dict.get(keyword)
        if res is None:
            return
        if use_random:
            return random.choice(res)
        else:
            if fetch_index >= len(res) or fetch_index < 0:
                return
            return res[fetch_index]
                    
    def add_new_keyword(self, keyword_match:str, content:str, user_id:int, tag_user_id:int=-1):
        if type(keyword_match) is not str or \
            len(keyword_match) < 1 or \
            type(content) is not str or\
            len(content) < 1:
            return "格式錯誤"
        elif len(keyword_match) > self.setting.max_keyword_length or \
             len(content) > self.setting.max_content_length:
                 return f"限制關鍵字長度{self.setting.max_keyword_length}字元, \
                          內容長度{self.setting.max_content_length}字元"
        elif keyword_match[0] in self.prefix_filter or \
             (keyword_match[0].isdigit() and len(keyword_match) < 3 ):
            return "請避免特殊字元開頭"
        elif self.user_count[user_id] > self.setting.limit_user_per_keyword and user_id not in self.maintainer_ids:
            return f"此使用者設定關鍵字超過 {self.setting.limit_user_per_keyword}, 目前只有管理者無上限"
        
        keyword_match = keyword_match.lower()
        if user_id not in self.maintainer_ids:
            if tag_user_id > 0 and user_id != tag_user_id:
                return "限制維護人員可以 tag 其他人"
        if user_id in self.maintainer_ids:
            user_id = -1
        key_lists = self.setting.key_mapping_dict[keyword_match]
        if len(key_lists) > self.setting.limit_content_pool_size_per_keyword:
            return f"限制每個關鍵字選擇數量為 {self.setting.limit_content_pool_size_per_keyword}"
        key_lists.append(KeyWordModel(
            content=content,
            set_user_id=user_id,
            tag_user_id=tag_user_id
        ))
        self._dump()
        return ""
        
    
    def del_keyword(self, keyword:str, index:int, user_id:int):
        keyword = keyword.lower()
        target = self.setting.key_mapping_dict.get(keyword)
        if target is None:
            return "找不到關鍵字"
        if index >= len(target) or index < 0:
            return "索引不正確"
        is_user_id_maintainer = user_id in self.maintainer_ids
        
        model = target[index]
        if model.set_user_id < 0 and is_user_id_maintainer is False:
            return "無法刪除管理者新增的關鍵字"
        if model.set_user_id != user_id and is_user_id_maintainer is False:
            return "無法刪除其他人創建的關鍵字"
        del target[index]
        if len(target) == 0:
            self.setting.key_mapping_dict.pop(keyword)
        self._dump()
        return ""
        