
import os
import json
import logging
from dotenv import load_dotenv
import ibm_boto3
from ibm_botocore.client import Config, ClientError
from utils import CommonUtils

class COS(object):

    def __init__(
        self,
        utils: CommonUtils
    ) -> None:
        load_dotenv()
        self.utils = utils
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(self.utils.cache['CONFIG']['LOGLEVEL'])
        self.COS_BUCKET_LOCATION = 'jp-tok-standard'
        self.COSAvailable = False

        if 'COS_API_KEY_ID' in self.utils.cache['CONFIG'] and 'COS_INSTANCE_CRN' in self.utils.cache['CONFIG']:
            if self.utils.cache['CONFIG']['COS_API_KEY_ID'] is not None and self.utils.cache['CONFIG']['COS_INSTANCE_CRN'] is not None:
                COS_ENDPOINT = self.utils.cache['CONFIG']['COS_ENDPOINT']
                COS_API_KEY_ID = self.utils.cache['CONFIG']['COS_API_KEY_ID']
                COS_INSTANCE_CRN = self.utils.cache['CONFIG']['COS_INSTANCE_CRN']
                try:
                    # Create client 
                    self.cos_cli = ibm_boto3.client("s3",
                        ibm_api_key_id=COS_API_KEY_ID,
                        ibm_service_instance_id=COS_INSTANCE_CRN,
                        config=Config(signature_version="oauth"),
                        endpoint_url=COS_ENDPOINT
                    )

                    self.COSAvailable = True

                except Exception as err:
                    self.logger.error("Error in Initializing Producer: >> ", err)

    def isCOSAvailable(self):
        self.logger.info('IN isCOSAvailable: %s', self.COSAvailable)
        return self.COSAvailable


    def get_buckets(self):
        print("Retrieving list of buckets")
        try:
            buckets = self.cos_cli.list_buckets()['Buckets']
            for bucket in buckets:
                print("Bucket Name: {0}".format(bucket))
        except ClientError as be:
            print("CLIENT ERROR: {0}\n".format(be))
        except Exception as e:
            print("Unable to retrieve list buckets: {0}".format(e))

    def create_bucket(self, bucket_name):
        print("Creating new bucket: {0}".format(bucket_name))
        
        try:
            self.cos_cli.Bucket(bucket_name).create(
                CreateBucketConfiguration={
                    "LocationConstraint": self.COS_BUCKET_LOCATION
                }
            )
            print("Bucket: {0} created!".format(bucket_name))
        except ClientError as be:
            print("CLIENT ERROR: {0}\n".format(be))
        except Exception as e:
            print("Unable to create bucket: {0}".format(e))
    
    def upload_file(self, bucket_name, item_name, file_path):
        try:
            self.logger.info('IN upload_file, bucket: %s, path: %s, key: %s', bucket_name, file_path, item_name)
            with open(file_path, 'rb') as data:
                self.cos_cli.upload_fileobj(data, bucket_name, 'frames/'+item_name)
                return 'https://{0}.s3.ap.cloud-object-storage.appdomain.cloud/frames/{1}'.format(bucket_name, item_name)
            # self.cos_cli.upload_file(Filename=file_path, Bucket='smartthings-detection', Key='FireFrame')
        except Exception as err:
            self.logger.error("Error in upload frame: >> %s", err)
            return False

    def multi_part_upload(self, bucket_name, item_name, file_path):
        try:
            print("Starting file transfer for {0} to bucket: {1}\n".format(item_name, bucket_name))
            # set 5 MB chunks
            part_size = 1024 * 1024 * 5

            # set threadhold to 15 MB
            file_threshold = 1024 * 1024 * 15

            # set the transfer threshold and chunk size
            transfer_config = ibm_boto3.s3.transfer.TransferConfig(
                multipart_threshold=file_threshold,
                multipart_chunksize=part_size
            )

            # the upload_fileobj method will automatically execute a multi-part upload
            # in 5 MB chunks for all files over 15 MB
            with open(file_path, "rb") as file_data:
                self.cos_cli.Object(bucket_name, item_name).upload_fileobj(
                    Fileobj=file_data,
                    Config=transfer_config
                )

            print("Transfer for {0} Complete!\n".format(item_name))
        except ClientError as be:
            print("CLIENT ERROR: {0}\n".format(be))
        except Exception as e:
            print("Unable to complete multi-part upload: {0}".format(e))

    def upload_large_file(self, bucket_name, item_name, file_path):
        print("Starting large file upload for {0} to bucket: {1}".format(item_name, bucket_name))

        # set the chunk size to 5 MB
        part_size = 1024 * 1024 * 5

        # set threadhold to 5 MB
        file_threshold = 1024 * 1024 * 5

        # set the transfer threshold and chunk size in config settings
        transfer_config = ibm_boto3.s3.transfer.TransferConfig(
            multipart_threshold=file_threshold,
            multipart_chunksize=part_size
        )

        # create transfer manager
        transfer_mgr = ibm_boto3.s3.transfer.TransferManager(self.cos_cli, config=transfer_config)

        try:
            # initiate file upload
            future = transfer_mgr.upload(file_path, bucket_name, item_name)

            # wait for upload to complete
            future.result()

            print ("Large file upload complete!")
        except Exception as e:
            print("Unable to complete large file upload: {0}".format(e))
        finally:
            transfer_mgr.shutdown()

