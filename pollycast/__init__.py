import feedparser
import logging
from feedgen.feed import FeedGenerator

from pollycast.bucket import Bucket
from pollycast.entry import Entry


def lambda_handler(event, _):
    rss = event['rss']
    bucket_name = event['bucket']
    logging.info(f"Processing url: {rss}")
    logging.info(f"Using bucket: {bucket_name}")

    bucket = Bucket(bucket_name)
    feed = feedparser.parse(rss)
    entries = [Entry(input_entry, bucket) for input_entry in feed.entries]

    feed_generator = init_feed_generator(feed)

    for entry in entries:
        try:
            feed_generator.add_entry(entry.as_feed_entry())
        except Exception as e:
            logging.error(f"Error while processing f{entry}", e)

    bucket.put_object(Key='podcast.xml', Body=feed_generator.rss_str(pretty=True))


def init_feed_generator(feed):
    feed_generator = FeedGenerator()
    feed_generator.load_extension('podcast')
    feed_generator.title("PocketCast")
    feed_generator.link(href=feed.feed.link, rel='alternate')
    feed_generator.subtitle(feed.feed.description or 'PocketCast')
    return feed_generator
