from typing import Any, Dict, List, Set
import attr

@attr.s
class RecordedMessageInfo:
    channel_type : str      = attr.ib(default="")
    is_message_exist     : bool    = attr.ib(default=True)
    can_notify_user_sets : Set[int] = attr.ib(default=attr.Factory(set))
    
    user_current_state   : Dict[int, Dict[str, Any]] = attr.ib(default=attr.Factory(dict))
    

@attr.s
class MessageSetting:
    message_id : int = attr.ib()
    channel_id : int = attr.ib()
    
    unique_symbol     : str  = attr.ib()
    subscribed_topic  : str  = attr.ib()
    
    message_runtime_info : RecordedMessageInfo = attr.ib(default=attr.Factory(RecordedMessageInfo))
    
    subscribed_args : Dict[str, Any]    = attr.ib(default=attr.Factory(dict))
    owner_ids : List[int]   = attr.ib(default=attr.Factory(list))
    
    
    @property
    def is_valid(self):
        return self.message_runtime_info.is_message_exist
    
    