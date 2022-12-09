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
from feedgen.feed import FeedGenerator
from flask import (request, url_for, current_app)


# Build an RSS feed and load the podcasst extension
def build_rss(posts):
    fg = FeedGenerator()
    fg.load_extension('podcast')
    fg.link(href=url_for('blog.index'))
    fg.podcast.itunes_author('Ben Brenner')
    fg.podcast.itunes_category([
        {'cat': 'Health &amp; Fitness', 'sub': 'Mental Health'},
    ])
    fg.podcast.itunes_complete('yes')
    fg.podcast.itunes_image(url_for('static', filename='podcast_image.jpg'))
    fg.title('Appreciative Narrative Daily Thought')
    fg.podcast.itunes_subtitle('Starting your day with a moment of appreciation')
    fg.description("""Adapting Appreciative Inquiry and Narrative Therapy into a daily transformative practice""")

    for post in posts:
        fe = fg.add_entry()
        fe.id(post['slug'])
        fe.title(post['title'])
        fe.description(post['body'])
        fe.enclosure( request.url_root + 'audio/' + post['audio'],  0, 'audio/mpeg')
    return(fg)

