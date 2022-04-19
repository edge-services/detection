

import os
import json
from dotenv import load_dotenv
from kafka import KafkaConsumer
import threading
from utils import CommonUtils

class Consumer(threading.Thread):

    def __init__(self, utils: CommonUtils):
        threading.Thread.__init__(self)
        self.stop_event = threading.Event()
        load_dotenv()
        self.utils = utils
        KAFKA_BROKERS=os.environ.get("kafka_brokers")
        sasl_mechanism = "PLAIN"
        kafka_username = os.environ.get("kafka_username")
        kafka_password = os.environ.get("kafka_password")
        security_protocol = "SASL_SSL"

        self.consumer = KafkaConsumer(bootstrap_servers=KAFKA_BROKERS,
                              security_protocol=security_protocol,
                              ssl_check_hostname=True,
                              ssl_cafile='./certs/Certificates.pem',
                              sasl_mechanism = sasl_mechanism,
                              sasl_plain_username = kafka_username,
                              sasl_plain_password = kafka_password,
                              group_id=self.utils.cache['thisDevice']['metadata']['entityCategoryId'],
                              auto_offset_reset='earliest', enable_auto_commit=True,
                            #   auto_commit_interval_ms=1000,
                              value_deserializer=lambda m: json.loads(m.decode('utf-8')))

    def stop(self):
        self.stop_event.set()
        self.consumer.close()
        print('Consumer Closed....')

    def run(self):
        topics = ['updates']
        try:
            self.consumer.subscribe(topics)
            while not self.stop_event.is_set():
                for message in self.consumer:
                    print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                                    message.offset, message.key,
                                                    message.value))
                    self.consumer.commit()
                    self.utils.cache['UPDATES'] = True
                    if self.stop_event.is_set():
                        print('Consumer Stopped >>>>> ')
                        break
        finally:
            self.consumer.close()
            print('Consumer Ended....')

