"""
Adapted from https://gist.github.com/om-henners/3547ce4e3432494e3eaa662e52355ee0
Simple app that generates a podcasst XML feed for Radicalized

To be fair this could be easily adapted to any audiobook / set of NP3s - you'd
just need to change the image, the path to the music and all the descriptions.

Requires:

- feedgen
- flask

Run using:

FLASK_APP=podcast_app FLASK_ENV=production flask run --host 0.0.0.0 --port 80

Then connect your podcast app to your computer's IP/index.xml and you're good
to go (i.e. http://<ipaddr>/index.xml).
"""
import os
from podgen import Podcast, Episode, Media, Person, Category, util
from flask import (request, url_for, current_app)
from datetime import datetime, timedelta
from dateutil.parser import parse
import pytz



# Build an RSS feed and load the podcast extension
def build_rss(posts):
    p = Podcast()
    p.name = "Doc to Pod"
    p.description = """Documents to Podcast"""
    p.website = url_for('blog.index', _external=True)
    p.explicit = False
    p.image = url_for('static', filename='appreciative_narrative.jpg', _external=True)
    p.copyright = "2023 Cobia Digital"
    p.language = "en-US"
    p.authors = [Person("Ben Brenner", "docpod@cobiadigital.com")]
    p.feed_url = url_for('blog.rss', _external=True)
    p.category = Category("Health &amp; Fitness", "Mental Health")
    p.owner = p.authors[0]

    for post in posts:
        ep = p.add_episode(Episode())
        ep.title = post['slug']
        ep.summary = "audio version of" + post['slug']
        ep.media = Media('https://docs-pod.cobiadigital.com/' + post['audio'],
                        size = str(post['audio_size']),
                        duration=timedelta(seconds=round(post['audio_size'] / 12000))
                        )
        ep.id= 'https://docs-pod.cobiadigital.com/' + post['audio']
        ep.link = url_for('blog.post_page',  id=post['id'], _external=True)
        ep.publication_date = parse(str(post['created'])).replace(tzinfo=pytz.UTC)
    return(p)

