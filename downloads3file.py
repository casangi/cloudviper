import boto3
from botocore import UNSIGNED
from botocore.client import Config
from botocore.handlers import disable_signing
import os 

#s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
#s3.download_file('viper-test-data','Antennae_North.cal.lsrk.split.vis.zarr"','/tmp/Antennae_North.cal.lsrk.split.vis.zarr"')

def downloadDirectoryFroms3(bucketName, remoteDirectoryName):
    s3_resource = boto3.resource('s3')
    s3_resource.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)
    bucket = s3_resource.Bucket(bucketName) 
    for obj in bucket.objects.filter(Prefix = remoteDirectoryName):
        if not os.path.exists(os.path.dirname(obj.key)):
            os.makedirs(os.path.dirname(obj.key))
        bucket.download_file(obj.key, obj.key) 

downloadDirectoryFroms3("viper-test-data", "s3://viper-test-data/Antennae_North.cal.lsrk.vis.zarr")