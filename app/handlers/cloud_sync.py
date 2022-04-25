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
    
    def __init__(
        self,
        utils: CommonUtils
    ) -> None:
        load_dotenv()
        self._tenant_id = os.environ.get("TENANT_ID")
        self._auth_svc_url = os.environ.get("auth_svc_url")
        self._iot_svc_url = os.environ.get("iot_svc_url")
        self._tokens = None
        self._thisDevice = None
        self.utils = utils
        
    @cached(cache, key=partial(hashkey, 'token'))
    def fetchToken(self):
        print('In fetchToken: >> ')
        endpoint =  self._auth_svc_url + '/api/'+self._tenant_id+'/clients/token'
        CLIENT_ID = os.environ.get("CLIENT_ID")
        CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
        PARAMS = {'clientId': CLIENT_ID, 'secret': CLIENT_SECRET}
        r = requests.post(url = endpoint, json = PARAMS)
        data = r.json()        
        self._tokens = {'token': data['token'], 'refreshToken': data['refreshToken']}
        self.saveLocal(self._tokens, 'tokens.json')
        return self._tokens

    @cached(cache, key=partial(hashkey, 'deviceData'))
    def fetchDeviceData(self, serialNumber):
        print('IN fetchDeviceData >> ')
        endpoint =  self._iot_svc_url + '/api/'+self._tenant_id+'/devices?filter=%s'        
        if self._tokens is None:
            self.fetchToken()
        headers = {'Authorization': 'Bearer '+self._tokens['token']}
        params={
                    "where": {
                        "metadata.tenantId": self._tenant_id,
                        "deviceSerialNo": serialNumber,
                        "status": "CLAIMED"
                    },
                    "offset": 0,
                    "limit": 10,
                    "skip": 0
                }
                
        params_json = json.dumps(params)
        r = requests.get(url = endpoint % params_json, headers=headers, params=params)
        devices = r.json()
        if devices and devices[0]:
            self._thisDevice = devices[0]
            self.saveLocal(self._thisDevice, 'thisDevice.json')   
        self.utils.cache['thisDevice'] = self._thisDevice 
        return self._thisDevice

    @cached(cache, key=partial(hashkey, 'attributes'))
    def fetchAttributes(self):
        attributes = []
        if self._thisDevice and self._thisDevice['id']:
            print('IN fetchAttributes, with deviceId >> ', self._thisDevice['id'])
            entityType = self._thisDevice['metadata']['entityType']
            endpoint =  self._iot_svc_url + '/api/'+self._tenant_id+'/'+entityType+'/attributes?filter=%s'        
            if self._tokens is None:
                self.fetchToken()
            headers = {'Authorization': 'Bearer '+self._tokens['token']}
            params={
                        "where": {
                            "type": "SHARED",
                            "metadata.entityType": entityType,
                            "metadata.entityCategoryId": self._thisDevice['metadata']['entityCategoryId'],
                            "metadata.tenantId": self._tenant_id
                        },
                        "fields": {
                            "id": True,
                            "type": True,
                            "key": True,
                            "dataType": True,
                            "defaultValue": True                        
                        },
                        "offset": 0,
                        "limit": 10,
                        "skip": 0
                    }
                
            params_json = json.dumps(params)
            r = requests.get(url = endpoint % params_json, headers=headers, params=params)
            attributes = r.json()
            self.saveLocal(attributes, 'attributes.json') 
        return attributes

    @cached(cache, key=partial(hashkey, 'rules'))
    def fetchRules(self):
        rules = []
        if self._thisDevice and self._thisDevice['id']:
            print('IN fetchRules, with deviceId >> ', self._thisDevice['id'])
            entityType = self._thisDevice['metadata']['entityType']
            endpoint =  self._iot_svc_url + '/api/'+self._tenant_id+'/rules?filter=%s'        
            if self._tokens is None:
                self.fetchToken()
            headers = {'Authorization': 'Bearer '+self._tokens['token']}
            params={
                        "where": {
                            "metadata.entityType": entityType,
                            "metadata.entityCategoryId": self._thisDevice['metadata']['entityCategoryId'],
                            "metadata.tenantId": self._tenant_id
                        },
                        "fields": {
                            "createdOn": False,
                            "modifiedOn": False,
                            "createdBy": False,
                            "modifiedBy": False
                        },
                        "offset": 0,
                        "limit": 10,
                        "skip": 0
                    }
                
            params_json = json.dumps(params)
            r = requests.get(url = endpoint % params_json, headers=headers, params=params)
            rules = r.json()
            self.saveLocal(rules, 'rules.json') 
        return rules

    def syncWithCloud(self):
        try:
            netAvailable = self.utils.is_connected()
            print('IN syncWithCloud, netAvailable: ', netAvailable)
            if netAvailable:
                self.cache.clear()
                serialNumber = self.utils.getserial()
                self._thisDevice = self.fetchDeviceData(serialNumber=serialNumber)
                # if self._thisDevice and self._thisDevice['id']:
                attributes = self.fetchAttributes()
                print('Total Attributes Fetched: >> ', len(attributes))
                self.updateAppConfig(attributes)
                self.downloadAIModel()
                rules = self.fetchRules()
                print('\nrules: >> ', rules)
                print('<<<<<< Data in Sync now with Cloud >>>>>>')
            else:
                print('Internet Not Available')
                self.syncWithLocal()
        except Exception as err:
            print('Exception in syncWithCloud: >> ', err)

    def syncWithLocal(self):
        self._thisDevice = self.loadData(self.utils.cache['CONFIG']['DATA_DIR'] + '/thisDevice.json')
        self.utils.cache['thisDevice'] = self._thisDevice 
        self.checkAIModel()
        print('<<<<<< Data in Sync now with local >>>>>>')

    def updateAppConfig(self, attributes):
        if attributes and len(attributes) > 0:
            for attrib in attributes:
                if attrib['type'] == 'SHARED':
                    if attrib['dataType'] == 'float':
                        self.utils.cache['CONFIG'][attrib['key']] = float(attrib['defaultValue'])
                    elif attrib['dataType'] == 'number':
                        self.utils.cache['CONFIG'][attrib['key']] = int(attrib['defaultValue'])
                    else:
                        self.utils.cache['CONFIG'][attrib['key']] = attrib['defaultValue']

    def saveLocal(self, data, fileName):
        json_object = json.dumps(data, indent = 4)       
        with open(os.path.join(self.utils.cache['CONFIG']['DATA_DIR'], fileName), "w") as outfile:
            outfile.write(json_object)

    def checkAIModel(self):        
        if(os.path.exists(self.utils.cache['CONFIG']['LOCAL_MODEL_PATH'])):
            return True

    def downloadAIModel(self):
        try:
            if 'DOWNLOAD_MODEL_PATH' in self.utils.cache['CONFIG'].keys():
                print('IN downloadAIModel, URL: >>  ', self.utils.cache['CONFIG']['DOWNLOAD_MODEL_PATH'])
                self.utils.downloadFile(self.utils.cache['CONFIG']['DOWNLOAD_MODEL_PATH'], self.utils.cache['CONFIG']['LOCAL_MODEL_PATH'])
        except Exception as err:
            print('Exception in downloadAIModel: >> ', err)

    def loadData(self, json_path):
        f = open(json_path)
        data = json.load(f)
        f.close()
        return data

    def publishToFlow(self, payload):
        # print("IN publishToFlow payload: ", payload); 
        if os.environ.get('FLOW_URL'):
            # print('IN publishToFlow: >> Event: ', payload['event'])
            try:
                r = requests.post(url = os.environ.get('FLOW_URL')+'/publish', json=payload)
                resp = r.json()
                print('PUBLISH RESPONSE: >> ', resp)
            except Exception as err:
                print(err)
           