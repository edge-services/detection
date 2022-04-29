

import os
import json
from dotenv import load_dotenv
from kafka import KafkaProducer

class Producer(object):

    def __init__(
        self
    ) -> None:
        load_dotenv()
        KAFKA_BROKERS=os.environ.get("kafka_brokers")
        sasl_mechanism = "PLAIN"
        kafka_username = os.environ.get("kafka_username")
        kafka_password = os.environ.get("kafka_password")
        security_protocol = "SASL_SSL"

        try:
            self.producer = KafkaProducer(bootstrap_servers=KAFKA_BROKERS,
                                security_protocol=security_protocol,
                                ssl_check_hostname=True,
                                ssl_cafile='./certs/Certificates.pem',
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

