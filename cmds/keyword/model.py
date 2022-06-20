from collections import defaultdict
from typing import DefaultDict, List
import attr

@attr.s
class KeyWordModel:
    content : str = attr.ib()
    tag_user_id : int = attr.ib(default=-1)
    set_user_id : int = attr.ib(default=-1)
    
    
@attr.s
class KeyWordSetting:
    key_mapping_dict : DefaultDict[str, List[KeyWordModel]] = attr.ib(default=attr.Factory(lambda : defaultdict(list)), repr=False)
    
    max_keyword_length : int = attr.ib(default=20)
    max_content_length : int = attr.ib(default=512)
    
    limit_user_per_keyword : int = attr.ib(default=50)
    limit_content_pool_size_per_keyword : int = attr.ib(default=100)