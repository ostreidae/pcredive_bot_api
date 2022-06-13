

# round-bobin schedule
from typing import List
import attr

@attr.s
class PeriodicSchedule:
    name : str = attr.ib()
    invoke_target_name : str = attr.ib()
    duration_ms        : int = attr.ib(default=60_000)
    priority           : int = attr.ib(default=100)
    enable             : bool = attr.ib(default=True)
    

@attr.s
class DailySchedule:
    name : str = attr.ib()
    invoke_target_name : str = attr.ib()
    invoke_utc_second_offset : int = attr.ib()
    invoke_weekedays   : List[int] = attr.ib(default=attr.Factory(lambda:[0,1,2,3,4,5,6]))
    priority           : int = attr.ib(default=100)
    enable             : bool = attr.ib(default=True)


@attr.s
class SpecialSchedule:
    name : str = attr.ib()
    invoke_target_name : str = attr.ib()
    invoke_timestamp_second : int = attr.ib()
    priority           : int = attr.ib(default=100)
