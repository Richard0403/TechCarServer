import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider

from config import settings


def upload_stream(stream, oss_file_name: str):
    """
    上传文件流
    """
    auth = oss2.Auth(settings.OSS_ACCESS_KEY, settings.OSS_ACCESS_SECRET)
    bucket = oss2.Bucket(auth, 'https://oss-cn-beijing.aliyuncs.com', 'xxxxx')
    bucket.put_object(oss_file_name, stream)


def upload_file(upload_file_name, oss_file_name: str):
    """
    上传文件
    """
    auth = oss2.Auth(settings.OSS_ACCESS_KEY, settings.OSS_ACCESS_SECRET)
    bucket = oss2.Bucket(auth, 'https://oss-cn-beijing.aliyuncs.com', 'xxxxx')
    with open(upload_file_name, 'rb') as file_obj:
        bucket.put_object(oss_file_name, file_obj)
