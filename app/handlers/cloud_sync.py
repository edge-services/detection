import os
import json
import requests
from dotenv import load_dotenv

class CloudSync(object):

    def __init__(
        self,
        CONFIG
    ) -> None:
        self.config = CONFIG
        load_dotenv()
        self._auth_svc_url = os.environ.get("auth_svc_url")
        self._iot_svc_url = os.environ.get("iot_svc_url")

    def fetchToken(self):
        endpoint =  self._auth_svc_url + '/api/ibm/clients/token'
        CLIENT_ID = os.environ.get("CLIENT_ID")
        CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
        PARAMS = {'clientId': CLIENT_ID, 'secret': CLIENT_SECRET}
        r = requests.post(url = endpoint, json = PARAMS)
        data = r.json()
        return data['token'], data['refreshToken']

    def fetchDeviceData(self):
        print('IN fetchDeviceData')
        endpoint =  self._iot_svc_url + '/api/ibm/devices?filter=%s'
        headers = {'Authorization': 'Bearer '+self._token_data['token']}
        params={
                    "where": {
                        "metadata.tenantId": "ibm",
                        "deviceSerialNo": "10000000f0d61812"
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
        token, refreshToken = self.fetchToken()
        self._token_data = {'token': token, 'refreshToken': refreshToken}
        json_object = json.dumps(self._token_data, indent = 4)  
        with open("./data/token_data.json", "w") as outfile:
            outfile.write(json_object)
    
        deviceData = self.fetchDeviceData()
        print(deviceData)
