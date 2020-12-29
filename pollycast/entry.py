import hashlib
import logging
from dataclasses import dataclass, field
from typing import Callable

import boto3
from boltons.cacheutils import cachedproperty
from feedgen.entry import FeedEntry
from feedparser import FeedParserDict
from newspaper import Article
from pollycast.bucket import Bucket
from pollycast.voice_utils import random_voice_id

SYNTHESIS_FORMAT = "mp3"


@dataclass
class Entry:
    input_entry: FeedParserDict
    bucket: Bucket
    polly: object = field(default_factory=lambda: boto3.client("polly"))
    article_supplier: Callable[[], Article] = Article

    def __getattr__(self, item):
        return self.input_entry.get(item)

    def as_feed_entry(self) -> FeedEntry:
        result = FeedEntry()
        result.id(self.id)
        result.link(href=self.link)
        result.content(self.content)
        result.title(self.title())
        result.published(self.published)
        result.enclosure(self.get_file_url(), 0, 'audio/mpeg')

        return result

    def get_file_url(self):
        return f"http://{self.bucket.name}.s3.amazonaws.com/{self.file_name}"

    @cachedproperty
    def file_name(self):
        if self.processed:
            logging.info(f"File with {self.id} id is found. Skipping transcription for this entry")
            return self.bucket.get_file(self.id)

        return self.synthesize_speech()

    def synthesize_speech(self):
        file_prefix = f"{self.id}.{self.voice}"
        response = self.polly.start_speech_synthesis_task(
            Engine="neural",
            Text=self.content,
            OutputFormat=SYNTHESIS_FORMAT,
            OutputS3BucketName=self.bucket.name,
            OutputS3KeyPrefix=file_prefix,
            VoiceId=self.voice
        )

        return f"{file_prefix}.{response['SynthesisTask']['TaskId']}.{SYNTHESIS_FORMAT}"

    def title(self):
        return self.input_entry['title'] + f". Read by {self.voice}"

    @cachedproperty
    def voice(self):
        return random_voice_id()

    @property
    def content(self):
        return f"{self.title()} by {self.authors}. Published on {self.published}.\n {self.article.text}"

    @property
    def authors(self):
        article_authors = " and ".join(self.article.authors)
        return self.input_entry.get('author', article_authors)

    @cachedproperty
    def article(self) -> Article:
        if self.processed:
            return FeedParserDict(authors='', text='')

        article = self.article_supplier(self.input_entry.link)

        if "content" in self.input_entry:
            article.set_html(self.input_entry.content[0].value)
            logging.info("Using inline content")
        else:
            logging.info(f"Getting content from: {self.input_entry.link}")
            article.download()

        article.parse()
        logging.debug("Just retrieved the following article: ")
        logging.debug(article)
        return article

    @cachedproperty
    def processed(self):
        return self.bucket.has_file(self.id)

    @cachedproperty
    def id(self):
        if "http" in self.input_entry.id:
            return self.md5(self.input_entry.id)

        return self.input_entry.id

    @staticmethod
    def md5(url):
        return hashlib.md5(str(url).encode("utf-8")).hexdigest()
