#Load Flask modules
from flask import (
    Blueprint, flash, g, redirect, Response, render_template, request, url_for
)
from werkzeug.exceptions import abort

#Load 3rd Party
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField
from feedgen.feed import FeedGenerator

#Load app functions
from ai_blog.db import get_db
from ai_blog.tts import create_mp3
from ai_blog.tts_voices import get_voices
from ai_blog.load_azure_client import load_speech_client, get_keys
from ai_blog.rss import build_rss


bp = Blueprint('blog', __name__)

speech_client = load_speech_client()

class PostForm(FlaskForm):
    title = StringField('Title')
    slug = StringField('Slug')
    body = CKEditorField('Body', validators=[DataRequired()])
    voice = SelectField('Voice',choices=[], validate_choice=True)
    submit = SubmitField('Submit')


@bp.route('/index.xml')
def get_feed():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, slug, body, voice, audio, created FROM post p ORDER BY created DESC'
    ).fetchall()
    fg = build_rss(posts)
    return Response(fg.rss_str(), mimetype='application/rss+xml')

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, voice, created FROM post p ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/voices', methods=('POST',))
def voices():
    voices_list = get_voices(speech_client)
    print(voices_list)
    db = get_db()
    db.executemany('INSERT INTO voices(id, voice_name) VALUES(?, ?);', voices_list)
    db.commit()
    return redirect(url_for('blog.create'))

@bp.route('/create', methods=('GET', 'POST'))
def create():
    form = PostForm()
    db = get_db()
    voice_list = db.execute('SELECT * FROM voices;').fetchall()
    form.voice.choices = [(voice[0],voice[1]) for voice in voice_list]
    if request.method == 'POST':
        title = form.title.data
        slug = form.slug.data
        body = form.body.data
        voice = form.voice.data
        error = None

        print(voice)
        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:

            db = get_db()
            result = db.execute(
                'INSERT INTO post (title, slug, body)'
                ' VALUES (?, ?, ?)',
                (title, slug, body)
            )
            db.commit()
            id = result.lastrowid
            audio = create_mp3(id, slug, body, voice, speech_client)
            db.execute(
                'UPDATE post SET audio = ?'
                'WHERE id = ?',
                (audio, id)
            )
            db.commit()
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

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
def update(id):
    post = get_post(id)
    form = PostForm()
    form.title.data = post['title']
    form.slug.data = post['slug']
    form.body.data = post['body']

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
                'UPDATE post SET title = ?, slug = ?, body = ?'
                'WHERE id = ?',
                (title, slug, body, id)
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