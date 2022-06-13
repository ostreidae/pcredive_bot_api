import asyncio
import logging
import threading
import aiohttp
from msgpack import packb, unpackb
from random import randint
from hashlib import md5, sha1
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
from base64 import b64encode, b64decode
from random import choice
from bs4 import BeautifulSoup
import requests
import re
import os
import json
import functools
from threading import Thread

import time
import attr
from sqlalchemy import true
from .utils import decryptxml

def get_headers():
    app_ver = get_ver()
    default_headers = {
        'Accept-Encoding' : 'gzip',
        'User-Agent' : 'Dalvik/2.1.0 (Linux, U, Android 5.1.1, PCRT00 Build/LMY48Z)',
        'Content-Type': 'application/octet-stream',
        'Expect': '100-continue',
        'X-Unity-Version' : '2018.4.21f1',
        'APP-VER' : app_ver,
        'BATTLE-LOGIC-VERSION' : '4',
        'BUNDLE-VER' : '',
        'DEVICE' : '2',
        'DEVICE-ID' : '7b1703a5d9b394e24051d7a5d4818f17',
        'DEVICE-NAME' : 'OPPO PCRT00',
        'GRAPHICS-DEVICE-NAME' : 'Adreno (TM) 640',
        'IP-ADDRESS' : '10.0.2.15',
        'KEYCHAIN' : '',
        'LOCALE' : 'Jpn',
        'PLATFORM-OS-VERSION' : 'Android OS 5.1.1 / API-22 (LMY48Z/rel.se.infra.20200612.100533)',
        'REGION-CODE' : '',
        'RES-VER' : '00017004'
    }
    return default_headers

# 获取版本号
def get_ver():
    app_url = 'https://apkimage.io/?q=tw.sonet.princessconnect'
    app_res = requests.get(app_url, timeout=15)
    soup = BeautifulSoup(app_res.text, 'lxml')
    ver_tmp = soup.find('span', text = re.compile(r'Version：(\d\.\d\.\d)'))
    app_ver = ver_tmp.text.replace('Version：', '')
    return str(app_ver)

def update_ver(root_dir=''):
    header_path = os.path.join(root_dir, 'headers.json')
    default_headers = get_headers()
    with open(header_path, 'w', encoding='UTF-8') as f:
        json.dump(default_headers, f, indent=4, ensure_ascii=False)
    #sv.logger.info(f'pcr-jjc3-tw的游戏版本已更新至最新')

async def gather_sequential(*coros):
    for coro in coros:
        await coro

class ApiException(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code
        self.message = message


class pcrclient:

    @staticmethod
    def _makemd5(str) -> str:
        return md5((str + 'r!I@nt8e5i=').encode('utf8')).hexdigest()
    
    def __init__(self, udid, short_udid, viewer_id, platform, proxy, root_dir=''):
        
        self.viewer_id = viewer_id
        self.short_udid = short_udid
        self.udid = udid
        self.headers = {}
        self.proxy = proxy
        

        header_path = os.path.join(root_dir, 'headers.json')
        with open(header_path, 'r', encoding='UTF-8') as f:
            defaultHeaders = json.load(f)
            
        for key in defaultHeaders.keys():
            self.headers[key] = defaultHeaders[key]

        self.headers['SID'] = pcrclient._makemd5(viewer_id + udid)
        self.apiroot = f'https://api{"" if platform == "1" else platform}-pc.so-net.tw'
        self.headers['platform'] = '1'

        self.shouldLogin = True
        self.last_login_time = 0
        self.login_lock = threading.Lock()
        self.login_async_lock = None
        self.async_session = None

    @staticmethod
    def createkey() -> bytes:
        return bytes([ord('0123456789abcdef'[randint(0, 15)]) for _ in range(32)])

    def _getiv(self) -> bytes:
        return self.udid.replace('-', '')[:16].encode('utf8')

    def pack(self, data: object, key: bytes) -> tuple:
        aes = AES.new(key, AES.MODE_CBC, self._getiv())
        packed = packb(data,
            use_bin_type = False
        )
        return packed, aes.encrypt(pad(packed, 16)) + key

    def encrypt(self, data: str, key: bytes) -> bytes:
        aes = AES.new(key, AES.MODE_CBC, self._getiv())
        return aes.encrypt(pad(data.encode('utf8'), 16)) + key

    def decrypt(self, data: bytes):
        data = b64decode(data.decode('utf8'))
        aes = AES.new(data[-32:], AES.MODE_CBC, self._getiv())
        return aes.decrypt(data[:-32]), data[-32:]

    def unpack(self, data: bytes):
        data = b64decode(data.decode('utf8'))
        aes = AES.new(data[-32:], AES.MODE_CBC, self._getiv())
        dec = unpad(aes.decrypt(data[:-32]), 16)
        return unpackb(dec,
            strict_map_key = False
        ), data[-32:]

    alphabet = '0123456789'

    @staticmethod
    def _encode(dat: str) -> str:
        return f'{len(dat):0>4x}' + ''.join([(chr(ord(dat[int(i / 4)]) + 10) if i % 4 == 2 else choice(pcrclient.alphabet)) for i in range(0, len(dat) * 4)]) + pcrclient._ivstring()

    @staticmethod
    def _ivstring() -> str:
        return ''.join([choice(pcrclient.alphabet) for _ in range(32)])

    def _get_crypted_data_header(self, apiurl:str, request:dict):
        key = pcrclient.createkey()
        if self.viewer_id is not None:
            request['viewer_id'] = b64encode(self.encrypt(str(self.viewer_id), key))

        packed, crypted_data = self.pack(request, key)
        headers = dict(self.headers)
        headers['PARAM'] = sha1((self.udid + apiurl + b64encode(packed).decode('utf8') + str(self.viewer_id)).encode('utf8')).hexdigest()
        headers['SHORT-UDID'] = pcrclient._encode(self.short_udid)
        return crypted_data, headers
        

    def callapi(self, apiurl: str, request: dict, noerr: bool = False, use_async=False):
        try:
            if use_async is False:
                return self._callapi(apiurl, request, noerr)
            else:
                return self._callapi_async(apiurl, request, noerr)
        except ApiException as exc:
            if exc.code is None or exc.code != "214":
                raise exc
            if use_async is False:
                self.login()
                return self._callapi(apiurl, request, noerr)
            else:
                return gather_sequential(
                    self.login_async(),
                    self._callapi_async(apiurl, request, noerr)
                )
            
    
    def _callapi(self, apiurl: str, request: dict, noerr: bool = False):
        url = self.apiroot + apiurl
        crypted, headers = self._get_crypted_data_header(apiurl, request)
        resp = requests.post(url, data=crypted, headers=headers)
        return self._parse_data(resp.content, url, noerr)
            
    async def _callapi_async(self, apiurl: str, request: dict, noerr: bool = False):
        crypted, headers = self._get_crypted_data_header(apiurl, request)
        url     = self.apiroot + apiurl
        session = self.async_session
        async with session.post(url, data=crypted, headers=headers) as resp:
            resp = await resp.read()
            return self._parse_data(resp, url, noerr)
        
    async def start_async_session(self):
        timeout = aiohttp.ClientTimeout(total=10)
        self.async_session = aiohttp.ClientSession(timeout=timeout)
        self.login_async_lock = asyncio.Lock()
    
    def _parse_data(self, response_bytes:bytes, apiurl="", noerr: bool = False):
        response = self.unpack(response_bytes)[0]
        data_headers = response['data_headers']

        if 'viewer_id' in data_headers:
            self.viewer_id = data_headers['viewer_id']

        if 'required_res_ver' in data_headers:
            self.headers['RES-VER'] = data_headers['required_res_ver']

        data = response['data']
        if not noerr and 'server_error' in data:
            data = data['server_error']
            code = data_headers['result_code']
            print(f'pcrclient: {apiurl} api failed code = {code}, {data}')
            raise ApiException(str(data), str(code))
        return data
    
    def login(self):
        if time.time() - self.last_login_time < 10:
            return
        with self.login_lock:
            self.callapi('/check/check_agreement', {})
            self.callapi('/check/game_start', {})
            self.callapi('/load/index', {
                'carrier': 'Android'
            })
            self.last_login_time = time.time()
    
    async def login_async(self):
        if time.time() - self.last_login_time < 10:
            return
        async with self.login_async_lock:
            p1 = self.callapi('/check/check_agreement', {}, use_async=True)
            p2 = self.callapi('/check/game_start', {}, use_async=True)
            p3 = self.callapi('/load/index', {
                'carrier': 'Android'
            }, use_async=True)
            await asyncio.gather(p1,p2,p3)
            self.last_login_time = time.time()

def get_logger(logger=None):
    if logger is None:
        return logging.getLogger()
    return logger

def get_pcr_client(root_dir=''):
    proxy_info = {
        "proxy": {
        
        }
    }
    update_ver(root_dir)
    xml_path = os.path.join(root_dir, 'shared_prefs/tw.sonet.princessconnect.v2.playerprefs.xml')
    acinfo_3cx = decryptxml(xml_path)
    client_3cx = pcrclient(acinfo_3cx['UDID'], 
                           acinfo_3cx['SHORT_UDID'], 
                           acinfo_3cx['VIEWER_ID'], 
                           acinfo_3cx['TW_SERVER_ID'], 
                           proxy_info['proxy'], 
                           root_dir=root_dir)
    return client_3cx
 
 
@attr.s
class PcrClientInfo:
    user_id : int = attr.ib(default=0)
    user_name : str = attr.ib(default="")
    pvp1_rank : int = attr.ib(default=15001)
    pvp1_group : int = attr.ib(default=0)
    
    pvp3_rank : int = attr.ib(default=15001)
    pvp3_group : int = attr.ib(default=0)
    
    last_login_time : int = attr.ib(default=0)
    last_login_idle_seconds : int = attr.ib(default=0)
    
    @staticmethod
    def from_dict(data_dict : dict) -> None:
        user_id = data_dict["user_info"]["viewer_id"]
        user_name = data_dict["user_info"]["user_name"]
        pvp1_rank = data_dict["user_info"]["arena_rank"]
        pvp1_group = data_dict["user_info"]["arena_group"]
        
        pvp3_rank = data_dict["user_info"]["grand_arena_rank"]
        pvp3_group = data_dict["user_info"]["grand_arena_group"]
        
        last_login_time = data_dict["user_info"]["last_login_time"]
        last_login_idle_seconds = int(time.time()) - last_login_time
        
        return PcrClientInfo(user_id=user_id,
                             user_name=user_name, 
                             pvp1_rank=pvp1_rank, 
                             pvp1_group=pvp1_group,
                             pvp3_rank=pvp3_rank,
                             pvp3_group=pvp3_group,
                             last_login_time=last_login_time, 
                             last_login_idle_seconds=last_login_idle_seconds)
        
    
class PcrClientApi:
    def __init__(self, root_dir='', logger=None, configuration_dict:dict=dict()):
        self.logger = get_logger(logger)
        self.api = get_pcr_client(root_dir)
        self.api.login()
        
        #thread_uploader = functools.partial(Thread, daemon=True)
        #self.schedule = PcrClientMaintainSchedule(self, thread_uploader, self.logger)
        
        self.cache_state = dict()
        self.config_dict = configuration_dict
        target_dict = configuration_dict.get("binding_id", dict())
        for key, val in dict(target_dict).items():
            target_dict[str(key)] = int(val)
        configuration_dict["binding_id"] = target_dict
        self.binding_id_dict =  target_dict
    
    @property
    def is_async_start(self):
        return self.api.async_session is not None
    
    async def start_async_session(self):
        await self.api.start_async_session()
        
    def dump_setting(self):
        with open("configuration.json", "w") as f:
            json.dump(self.config_dict, f, sort_keys=true, indent=4)
            
    def _get_from_cache(self, game_id):
        current_ts = (time.time()*1e3)
        last_state = self.cache_state.get(game_id, None)
        if last_state is not None:
            res, ts = last_state
            if current_ts - ts < 60*1000:
                if type(res) is Exception or type(res) is ApiException:
                    raise res
                return res
        return None
    
    def _process_except(self, game_id:int, err:Exception):
        if type(err) is ApiException:
            err : ApiException = err
            if err.code is None or err.code != "214":
                self.cache_state[game_id] = (err, int(time.time()*1e3))
            raise err            
        else:
            self.cache_state[game_id] = (err, int(time.time()*1e3))
            raise err
        
    async def login_async(self):
        await self.api.login_async()
            
    async def query_target_user_game_id_async(self, game_id:int, use_cache=True):
        if use_cache:
            last_state = self._get_from_cache(game_id)
            if last_state is not None:
                return last_state
        try:
            res = await self.api.callapi('/profile/get_profile', {'target_viewer_id': int(game_id)}, use_async=True)
            ts  = int(time.time()*1e3)
            res = PcrClientInfo.from_dict(res)
        except Exception as err:
            self._process_except(game_id, err)
            
        self.cache_state[game_id] = (res, ts)
        return res
        
        
    def query_target_user_game_id_fromdc(self, dc_id:int) -> PcrClientInfo:
        game_id = self.binding_id_dict.get(dc_id, None)
        if game_id is None:
            return
        return self.query_target_user_game_id(game_id)
        
    def bind_user_id(self, dc_id, game_id):
        dc_id = str(dc_id)
        if self.binding_id_dict.get(dc_id, 0) == game_id:
            return
        self.binding_id_dict[dc_id] = game_id
        self.dump_setting()
    

#TODO: maintain user rank history
class PcrClientMaintainSchedule:
    def __init__(self, inst:PcrClientApi, thread_func_uploader, logger=None):
        self.inst = inst
        self.logger = logger
        self.thread = thread_func_uploader(target=self.main_timer)
        
    def main_timer(self):
        pass
    
    
        
        