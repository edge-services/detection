

import os
import json
from dotenv import load_dotenv

from kafka import KafkaProducer

from utils import CommonUtils

class Producer(object):

    utils = CommonUtils()

    def __init__(
        self,
        thisDevice
    ) -> None:
        load_dotenv()
        self.thisDevice = thisDevice
        # topic = "updates"
        KAFKA_BROKERS=os.environ.get("kafka_brokers")
        sasl_mechanism = "PLAIN"
        kafka_username = os.environ.get("kafka_username")
        kafka_password = os.environ.get("kafka_password")
        security_protocol = "SASL_SSL"

        self.producer = KafkaProducer(bootstrap_servers=KAFKA_BROKERS,
                             security_protocol=security_protocol,
                             ssl_check_hostname=True,
                             ssl_cafile='./certs/Certificates.pem',
                             sasl_mechanism=sasl_mechanism,
                             sasl_plain_username=kafka_username,
                             sasl_plain_password=kafka_password)
    
    def publish(self, topic, payload):
        jd = json.dumps(payload).encode('utf-8')
        self.producer.send(topic, jd)
        self.producer.flush()

