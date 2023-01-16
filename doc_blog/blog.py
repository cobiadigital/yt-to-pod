#Load Flask modules
from flask import (
    Blueprint, flash, g, redirect, Response, render_template, request, url_for, send_from_directory,
    current_app, send_file
)
from werkzeug.exceptions import abort
import os
#Load 3rd Party
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField
from feedgen.feed import FeedGenerator
from werkzeug.utils import secure_filename


#Load app functions
from doc_blog.db import get_db
from doc_blog.tts import create_mp3
from doc_blog.tts_voices import get_voices
from doc_blog.load_azure_client import load_speech_client, get_keys
from doc_blog.rss import build_rss
from flask_frozen import Freezer


bp = Blueprint('blog', __name__)

speech_client = load_speech_client()

class PostForm(FlaskForm):
    slug = StringField()
    file = FileField()
    voice = SelectField('Voice',choices=[], validate_choice=True)
    submit = SubmitField('Submit')


@bp.route('/rss.xml')
def rss():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, slug, voice, response, audio, created, audio_size FROM post p ORDER BY created DESC'
    ).fetchall()
    fg = build_rss(posts)
    return Response(fg.rss_str(), mimetype='application/rss+xml')

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, slug, voice, response, audio, created, audio_size FROM post p ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/voices', methods=('GET', 'POST'))
def voices():
    if request.method == 'POST':
        voices_list = get_voices(speech_client)
        db = get_db()
        db.executemany('INSERT INTO voices(id, voice_name) VALUES(?, ?);', voices_list)
        db.commit()
        return redirect(url_for('blog.create'))
    return redirect(url_for('blog.index'))

@bp.route('/create', methods=('GET', 'POST'))
def create():
    form = PostForm()

    if request.method == 'GET':
        db = get_db()
        voice_list = db.execute('SELECT * FROM voices;').fetchall()

        form.voice.choices = [(voice[0],voice[1]) for voice in voice_list]
#         form.voice.data = defaults['voice']

    if request.method == 'POST':
        slug = form.slug.data
        filename = form.file.name
        if form.file.data:
            response = request.files[form.file.name].read()
        voice = form.voice.data
        error = None

        print(voice)

        if error is not None:
            flash(error)
        else:
            db = get_db()
            result = db.execute(
                'INSERT INTO post (slug, filename, response)'
                ' VALUES (?, ?, ?)',
                (slug, filename, response)
            )
            db.commit()
            id = result.lastrowid

            audio_list = create_mp3(id, slug, filename, response, voice, speech_client)
            db.execute(
                'UPDATE post SET audio = ?, audio_size = ?'
                'WHERE id = ?',
                (audio_list[0],audio_list[1], id)
            )
            db.commit()
            os.system("python freeze.py")
            os.system("git status")
            os.system("git add -A")
            os.system('git commit -m "' + slug + '"' )
            os.system("git push")

            return redirect(url_for('blog.index'))

    return render_template('blog/create.html', form=form)


def get_post(id):
    post = get_db().execute(
        'SELECT id, title, slug, body, created'
        ' FROM post WHERE id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    return post

@bp.route('/<int:id>/', methods=('GET',))
def post_page(id):
    post = get_post(id)
    audio_store_url = current_app.config.get_namespace('AUDIO_STORE_URL')

    return render_template('blog/post_page.html', post=post, audio_store_url=audio_store_url)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
def update(id):
    ckeditor = CKEditor()
    post = get_post(id)
    form = PostForm()
    form.title.data = post['title']
    form.slug.data = post['slug']
    form.cold_open.data = post['cold_open']
    form.cold_open.data = post['intro']
    form.body.data = post['body']
    form.ending.data = post['ending']

    if request.method == 'POST':
        title = form.title.data
        slug = form.slug.data
        body = form.body.data
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, slug = ?, cold_open = ?, intro = ?, body = ?, ending = ?'
                'WHERE id = ?',
                (title, slug, cold_open, intro, body, ending, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post, form=form)

@bp.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

