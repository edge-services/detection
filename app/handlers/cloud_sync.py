import os
import json
import requests
from dotenv import load_dotenv
from cachetools import cached, TTLCache
from cachetools.keys import hashkey
from functools import partial

from utils import CommonUtils

class CloudSync(object):

    cache = TTLCache(maxsize=100, ttl=86400)
    utils = CommonUtils()

    def __init__(
        self,
        CONFIG
    ) -> None:
        self.config = CONFIG
        load_dotenv()
        self._tenant_id = os.environ.get("TENANT_ID")
        self._auth_svc_url = os.environ.get("auth_svc_url")
        self._iot_svc_url = os.environ.get("iot_svc_url")
        self._token_data = None

    @cached(cache, key=partial(hashkey, 'token'))
    def fetchToken(self, saveLocal = True):
        print('In fetchToken: >> ')
        endpoint =  self._auth_svc_url + '/api/'+self._tenant_id+'/clients/token'
        CLIENT_ID = os.environ.get("CLIENT_ID")
        CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
        PARAMS = {'clientId': CLIENT_ID, 'secret': CLIENT_SECRET}
        r = requests.post(url = endpoint, json = PARAMS)
        data = r.json()
        if saveLocal == True:
            self._token_data = {'token': data['token'], 'refreshToken': data['refreshToken']}
            json_object = json.dumps(self._token_data, indent = 4)  
            with open("./data/token_data.json", "w") as outfile:
                outfile.write(json_object)
        return self._token_data

    @cached(cache, key=partial(hashkey, 'deviceData'))
    def fetchDeviceData(self, serialNumber):
        print('IN fetchDeviceData >> ')
        endpoint =  self._iot_svc_url + '/api/'+self._tenant_id+'/devices?filter=%s'        
        if self._token_data is None:
            self.fetchToken(saveLocal = True)
        headers = {'Authorization': 'Bearer '+self._token_data['token']}
        params={
                    "where": {
                        "metadata.tenantId": self._tenant_id,
                        "deviceSerialNo": serialNumber
                    },
                    "offset": 0,
                    "limit": 10,
                    "skip": 0
                }
                
        params_json = json.dumps(params)
        r = requests.get(url = endpoint % params_json, headers=headers, params=params)
        return r.json()

    @cached(cache, key=partial(hashkey, 'attributes'))
    def fetchAttributes(self, entityType='DEVICE', deviceId=None):
        print('IN fetchAttributes, with deviceId >> ', deviceId)
        endpoint =  self._iot_svc_url + '/api/'+self._tenant_id+'/'+entityType+'/attributes?filter=%s'        
        if self._token_data is None:
            self.fetchToken(saveLocal = True)
        headers = {'Authorization': 'Bearer '+self._token_data['token']}
        params={
                    "where": {
                        "type": "SHARED",
                        "metadata.entityType": "DEVICE",
                        "metadata.accountId": {"neq": ""},
                        "metadata.tenantId": self._tenant_id,
                        "metadata.entityId": deviceId
                    },
                    "offset": 0,
                    "limit": 10,
                    "skip": 0
                }
                
        params_json = json.dumps(params)
        r = requests.get(url = endpoint % params_json, headers=headers, params=params)
        return r.json()

    def syncWithCloud(self):
        print('IN syncWithCloud')
        self.cache.clear()
        serialNumber = self.utils.getserial()
        devices = self.fetchDeviceData(serialNumber=serialNumber)
        if devices and devices[0]:
            thisDevice = devices[0]
        # print('thisDevice: >> ', thisDevice)
        attributes = self.fetchAttributes(entityType='DEVICE', deviceId=thisDevice['id'])
        print('attributes: >> ', attributes)
        
