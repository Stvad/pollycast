from dataclasses import dataclass, field
from typing import Callable

from boltons.cacheutils import cachedproperty
from fleece import boto3


@dataclass
class Bucket:
    name: str
    bucket_provider: Callable[[str], object] = lambda bucket_name: boto3.resource('s3').Bucket(bucket_name)
    s3_bucket: object = field(init=False)

    def __post_init__(self):
        self.s3_bucket = self.bucket_provider(self.name)

    @cachedproperty
    def files(self) -> dict:
        files = (o.key for o in self.s3_bucket.objects.all())
        return {file.split('.')[0]: file for file in files}

    def has_file(self, id):
        return id in self.files

    def get_file(self, id):
        return self.files.get(id)
