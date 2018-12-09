import random
import sys

from newspaper import Article, ArticleException

sys.path.insert(0, './_build')

import logging

import feedparser
import dateutil.parser
import hashlib
from feedgen.feed import FeedGenerator
from botocore.exceptions import BotoCoreError

from fleece import boto3
from fleece.xray import (monkey_patch_botocore_for_xray)

logging.basicConfig(level=logging.INFO)
logging.getLogger("boto3").setLevel(logging.WARNING)

monkey_patch_botocore_for_xray()

MAX_TPS = 10
MAX_CONCURRENT_CONNECTIONS = 20
TASKS = 100
REQUEST_LIMIT = 99900  # https://docs.aws.amazon.com/polly/latest/dg/limits.html


def article_from_entry(entry):
    article = Article(entry.link)

    if "content" in entry:
        article.set_html(entry.content[0].value)
        logging.info("Using inline content")
    else:
        logging.info(f"Getting content from: {entry.link}")
        article.download()

    article.parse()
    logging.debug("Just retrieved the following article: ")
    logging.debug(article)
    return article


def get_entries(feed: feedparser.FeedParserDict):
    for entry in feed.entries:
        try:
            update_entry_id(entry)

            article = article_from_entry(entry)
            authors = " and ".join(article.authors)

            # todo ssml for things
            yield dict(
                content=f"{entry.title} by {entry.get('author', authors)}. Published on {entry.published}.\n { article.text }",
                id=entry.id,
                title=entry.title,
                link=entry.link,
                published=(dateutil.parser.parse(entry.published)),
            )
        except ArticleException as e:
            logging.error(e)


def update_entry_id(entry):
    if "http" in entry.id:
        nid = hashlib.md5(str(entry.id).encode("utf-8"))
        entry.id = nid.hexdigest()


def lambda_handler(event, _):
    rss = event['rss']
    bucket_name = event['bucket']
    logging.info(f"Processing url: {rss}")
    logging.info(f"Using bucket: {bucket_name}")

    polly = boto3.client("polly")
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    files = get_files_grouped_by_prefix(bucket)

    feed = feedparser.parse(rss)

    feed_generator = init_feed_generator(feed)

    for entry in get_entries(feed):
        try:
            # todo consider reading the generated feed first to get all the info from it instead of

            id_prefix = entry['id']

            file_name = files.get(id_prefix)

            voice_id = get_voice_id()  # todo get from filename/metadata

            feed_entry = feed_generator.add_entry()
            feed_entry.id(entry['id'])
            feed_entry.link(href=entry['link'])
            feed_entry.content(entry['content'])
            feed_entry.title(entry['title'] + f". Read by {voice_id}")
            feed_entry.published(entry['published'])

            if file_name is None:
                file_prefix = f"{id_prefix}.{voice_id}"
                response = polly.start_speech_synthesis_task(
                    Text=entry['content'],
                    OutputFormat="mp3",
                    OutputS3BucketName=bucket_name,
                    OutputS3KeyPrefix=file_prefix,
                    VoiceId=voice_id
                )

                file_name = f"{file_prefix}.{response['SynthesisTask']['TaskId']}.mp3"
            else:
                logging.info(f"{file_name} is found. Skipping an entry with corresponding id")

            entry_url = f"http://{bucket_name}.s3.amazonaws.com/{file_name}"  # todo mp3 is hardcoded
            feed_entry.enclosure(entry_url, 0, 'audio/mpeg')
        except BotoCoreError as error:
            logging.error(error)

    bucket.put_object(Key='podcast.xml', Body=feed_generator.rss_str(pretty=True))


def get_files_grouped_by_prefix(bucket):
    logging.info("getting list of existing objects in the given bucket")
    files = (o.key for o in bucket.objects.all())

    return {file.split('.')[0]: file for file in files}


def get_voice_id():
    # todo how do I prioritize some?
    return random.choice(["Salli", "Salli", "Joey", "Justin", "Matthew", "Ivy", "Joanna", "Kendra", "Kimberly", "Amy",
                          "Emma", "Brian", "Geraint", "Nicole", "Russell"])


def init_feed_generator(feed):
    feed_generator = FeedGenerator()
    feed_generator.load_extension('podcast')
    feed_generator.title("PocketCast")
    feed_generator.link(href=feed.feed.link, rel='alternate')
    feed_generator.subtitle(feed.feed.description)
    return feed_generator
