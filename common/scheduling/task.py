from __future__ import annotations 

import asyncio
import threading
from typing import Callable, Coroutine, List, Union, Any
import logging
import traceback

from .async_class import AsyncClass

def _get_logger(logger=None):
    if logger is None:
        return logging.getLogger() #root logger
    return logger

def convert_callback(callback:Callable):
    if callback is None:
        return lambda : None
    return callback

class Task(AsyncClass):
    def __init__(self, 
                 coro_callable:Callable[[None], Coroutine], 
                 done_callback:Union[Callable, None]=None):
        self.done_percent = 0.
        self.coro_callable = coro_callable
        self._loop = asyncio.get_event_loop()
        self._async_task = None
        
        #TODO: wrap done_callback
        self.done_callback = convert_callback(done_callback)
        
    @property
    def is_task_start(self):
        return self._async_task is not None

    async def __ainit__(self, *args: Any, **kwargs: Any):
        await self.direct_run()
        
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.__ainit__(*args, **kwds)
    
    def run_as_background(self):
        coro = self.coro_callable()
        self._async_task = self._loop.create_task(coro)
        self._async_task.add_done_callback(self.done_callback)
        return self._async_task

    async def direct_run(self, timeout_seconds = 0.):
        if timeout_seconds > 1e-3:
            await asyncio.wait_for(
                self.coro_callable(),
                timeout=timeout_seconds)
        else:
            await self.coro_callable()
        self.done_callback()

    @staticmethod
    def gather(task_list : List[Task], 
                      delay_second_between=0, 
                      timeout_second_each_task=3, 
                      sequential=True) -> Task:
        async def run_task_list():
            if sequential:
                for t in task_list:
                    await t.direct_run(timeout_second_each_task)
                    if delay_second_between >= 1e-3:
                        await asyncio.sleep(delay_second_between)
            else:
                all_tasks = [t.run_as_background() 
                                for t in task_list ]
                await asyncio.gather(*all_tasks)
        return Task(run_task_list)


class BackgroundTask(AsyncClass):
    def __init__(self, 
                main_coro_callable:Callable[[None], Coroutine], 
                max_timeout_seconds = 5,
                name = "main",
                logger = None):
        self.name = name
        self.max_timeout_seconds = max_timeout_seconds
        self.main_coro_caller = main_coro_callable
        self.logger = _get_logger(logger)

    async def __ainit__(self, *args: Any, **kwargs: Any):
        await self.run(*args, **kwargs)
        
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.__ainit__(*args, **kwds)
    
    async def run(self, *args, **kwargs):
        try:
            if self.max_timeout_seconds <= 0:
                return await self.main_coro_caller(*args, **kwargs)
        except TimeoutError:
            self.logger.warn(f"background task {self.name} \
                exceed {self.max_timeout_seconds} seconds timeout ")
        except Exception:
            err_trace = traceback.format_exc()
            self.logger.error(err_trace)
    

class DirectTask(AsyncClass):
    def __init__(self, 
                main_callable:Callable, 
                max_timeout_seconds = 5,
                name = "main",
                logger = None):
        self.name = name
        self.main_callable = main_callable
        self.logger = _get_logger(logger)

    async def __ainit__(self, *args: Any, **kwargs: Any):
        await self.run(*args, **kwargs)
        
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.__ainit__(*args, **kwds)
    
    async def run(self, *args, **kwargs):
        try:
            return self.main_callable(*args, **kwargs)
        except Exception:
            err_trace = traceback.format_exc()
            self.logger.error(err_trace)