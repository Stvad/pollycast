from unittest.mock import Mock

from expects import expect, be
from mamba import description, it

from pollycast.bucket import Bucket

with description("Bucket"):
    with it("should report file present when it is and return it"):
        episode_id = "episode_id"
        file_name = f"{episode_id}.voice_id.etc"
        s3_bucket = Mock()
        s3_bucket.objects.all.return_value = [Mock(key=file_name)]
        bucket = Bucket("test_name", Mock(return_value=s3_bucket))

        expect(bucket.has_file(episode_id)).to(be(True))
        expect(bucket.get_file(episode_id)).to(be(file_name))
