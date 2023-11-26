#Load Flask modules
from flask import (
    Blueprint, flash, g, redirect, Response, render_template, request, url_for, send_from_directory,
    stream_with_context, current_app, send_file
)

#Load 3rd Party
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, IntegerField, RadioField, HiddenField
from wtforms.validators import DataRequired
from sqlalchemy.exc import SQLAlchemyError
import keyring
import boto3
from botocore.exceptions import ClientError
from pathvalidate import sanitize_filename
from queue import Queue

#Load app functions
from . import db
from .rss import build_rss
from .ytdl import get_yt_info, get_yt_download
from .models import Post

import os
import time

bp = Blueprint('blog', __name__)

search = None

task_status = {"status": "not started"}

def get_s3client():
    try:
        url = os.getenv("S3_URL")
    except:
        url = keyring.get_keyring('cloudflare_ytpod', 'url')
    try:
        aws_access_key_id = os.getenv("ACCESS_KEY_ID")
    except:
        aws_access_key_id = keyring.get_password('cloudflare_ytpod', "ACCESS_KEY_ID")
    try:
        aws_secret_access_key = os.getenv("ACCESS_KEY_SECRET")
    except:
        aws_secret_access_key = keyring.get_password('cloudflare_ytpod', "ACCESS_KEY_SECRET")

    s3 = boto3.client('s3',
      endpoint_url = url,
      aws_access_key_id = aws_access_key_id,
      aws_secret_access_key = aws_secret_access_key
    )
    return s3

class GetUrlForm(FlaskForm):
    get_url = StringField('URL of Youtube Video or Playlist')
    submit = SubmitField('Submit')

class VideoSelectForm(FlaskForm):
    videos = SelectMultipleField('Videos', choices=[], validate_choice=True)
    submit = SubmitField('Submit')

@bp.route('/rss.xml')
def rss():
    fg = build_rss(db.session.query(Post).order_by(Post.created.desc()).all())
    return Response(fg.rss_str(), mimetype='application/rss+xml')

@bp.route('/')
def index():
    posts = db.session.query(Post).order_by(Post.created.desc()).all()
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
def create():
    get_url_form = GetUrlForm()
    return render_template('blog/create.html', get_url_form=get_url_form)


# Global queue for SSE messages
sse_queue = Queue()
#Global variable for yt_info
yt_info = None
@bp.route('/url_results', methods=('POST',))
def url_results():
    task_status["status"] = "Looking up URL"
    print(task_status)
    # Simulate a long running task
    sse_queue.put(task_status)
    global yt_info
    yt_info = get_yt_info(request.form['get_url'])
    task_status["status"] = "completed"
    print(task_status)
    sse_queue.put(task_status)
    video_select_form = VideoSelectForm()
    for i, video in enumerate(yt_info['entries']):
         video_select_form.videos.choices.append((i, video['title']))
#    return '', 204
    return render_template('partials/url_results.html', video_select_form=video_select_form )

@bp.route('/select_videos', methods=('POST',))
def select_videos():
    video_select_form = VideoSelectForm()
    selected_videos = video_select_form.videos.data
    print(selected_videos)
    codec = 'mp3'
    for playlist_int in selected_videos:
        global yt_info
        video_info = yt_info['entries'][int(playlist_int)]
        file_name = sanitize_filename(f'''
            {video_info["playlist_index"]}-{video_info["n_entries"]} {video_info["title"]}.{codec}
            ''')
        try:
            error = get_yt_download(video_info['id'], file_name)
            print(error)
        except Exception as e:
            print(e)
        if not error:
            db.session.add(
                Post(title=video_info['title'],
                     slug=video_info['id'],
                     playlist_name=video_info['playlist'],
                     playlist_id=video_info['playlist_id'],
                     playlist_i=video_info['playlist_index'],
                     playlist_n=video_info['n_entries'],
                     duration_s=video_info['duration'],
                     body=video_info['description'],
                     audio=file_name,
                ))
            try:
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                print(str(e))
            s3 = get_s3client()
            bucket = 'ytpod'
            try:
                s3.upload_file(f'downloads/{file_name}', bucket, format(file_name))
            except ClientError as e:
                print(e)
            # os.remove(f'downloads/{file_name}')
            task_status["track"] = file_name
            sse_queue.put(task_status)
    return redirect(url_for('blog.index'))

@bp.route('/sse')
def sse():
    return Response(stream_with_context(event_stream()),
                    mimetype="text/event-stream")
def event_stream():
    while True:
        # Wait for new data in the queue
        data = sse_queue.get()
        yield f"message: {data}\n\n"

def long_running_task(url):
    task_status["status"] = "running"
    # Simulate a long running task
    get_yt_info()
    time.sleep(10)
    task_status["status"] = "completed"

def task_status_stream():
    while True:
        yield f"data: {task_status['status']}\n\n"
        time.sleep(1)


@bp.route('/<int:id>/', methods=('GET',))
def post_page(id):
    post = db.first_or_404(Post, id=id)
    audio_store_url = current_app.config.get_namespace('AUDIO_STORE_URL')
    return render_template('blog/post_page.html', post=post, audio_store_url=audio_store_url)
