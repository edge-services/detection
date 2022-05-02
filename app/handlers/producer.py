

import os
import json
from dotenv import load_dotenv
from kafka import KafkaProducer
from utils import CommonUtils

class Producer(object):

    def __init__(
        self,
        utils: CommonUtils
    ) -> None:
        load_dotenv()
        self.utils = utils
        sasl_mechanism = "PLAIN"
        security_protocol = "SASL_SSL"
        KAFKA_BROKERS= self.utils.cache['CONFIG']['kafka_brokers']        
        kafka_username = self.utils.cache['CONFIG']['kafka_username']
        kafka_password = self.utils.cache['CONFIG']['kafka_password'] 

        try:
            self.producer = KafkaProducer(bootstrap_servers=KAFKA_BROKERS,
                                security_protocol=security_protocol,
                                ssl_check_hostname=True,
                                ssl_cafile=self.utils.cache['CONFIG']['kafka_certs_path'],
                                sasl_mechanism=sasl_mechanism,
                                sasl_plain_username=kafka_username,
                                sasl_plain_password=kafka_password)
        except Exception as err:
            print("Error in Initializing Producer: >> ", err)
    
    def publish(self, topic, payload):
        try:
            jd = json.dumps(payload).encode('utf-8')
            self.producer.send(topic, jd)
            self.producer.flush()
        except Exception as err:
            print("Error in publishing: >> ", err)

