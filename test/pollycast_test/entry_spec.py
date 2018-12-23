from collections import defaultdict
from unittest.mock import Mock

from expects import expect, contain, equal, be
from feedparser import FeedParserDict
from mamba import description, it

from pollycast.entry import Entry

EXAMPLE_ID = "example_id"
BASIC_INPUT_ENTRY = FeedParserDict(id=EXAMPLE_ID)


def mock_bucket(has_file=False, file_name=None):
    bucket = Mock()
    bucket.has_file = Mock(return_value=has_file)
    bucket.get_file = Mock(return_value=file_name)
    return bucket


with description("Entry"):
    with it("should hash http-link form id's"):
        http_id = "http://example.com"
        entry = Entry(FeedParserDict(id=http_id), None)

        expect(entry.id).not_to(contain("http"))

    with it("should not change it if it is does not contain http"):
        entry = Entry(BASIC_INPUT_ENTRY, None)

        expect(entry.id).to(equal(EXAMPLE_ID))

    with it("should be marked as processed if the file with given id is in the bucket"):
        entry = Entry(BASIC_INPUT_ENTRY, mock_bucket(True))

        expect(entry.processed).to(be(True))

    with it("should redirect unset fields to input_entry"):
        test_field = "whee"
        entry = Entry(FeedParserDict(id=EXAMPLE_ID, test_field=test_field), None)

        expect(entry.test_field).to(equal(test_field))

    with it("should use file in the bucket if the file for given id exists"):
        file_name = "mock_file_name"
        bucket = mock_bucket(True, file_name)
        entry = Entry(BASIC_INPUT_ENTRY, bucket)
        entry.file_name

        bucket.get_file.assert_called_with(EXAMPLE_ID)

    with it("should call polly to do synthesis when no previous recording for the entry found"):
        bucket = mock_bucket(False)
        polly = Mock()
        entry = Entry(BASIC_INPUT_ENTRY, bucket, polly)

        polly.start_speech_synthesis_task = Mock(return_value=defaultdict(lambda: defaultdict(dict)))

        entry.file_name

        polly.start_speech_synthesis_task.assert_called()
