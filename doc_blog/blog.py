#Load Flask modules
from flask import (
    Blueprint, flash, g, redirect, Response, render_template, request, url_for, send_from_directory,
    current_app, send_file
)
from datetime import datetime
from werkzeug.exceptions import abort
import os
import AO3
from doc_blog.tts import create_mp3

#Load 3rd Party
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, IntegerField
from wtforms.validators import DataRequired
from feedgen.feed import FeedGenerator
from werkzeug.utils import secure_filename

import shelve

#Load app functions
from . import db
from .tts import create_mp3, synthesize_ssml
from .tts_voices import get_voices
from .load_azure_client import load_speech_client, get_keys
from .rss import build_rss
# from flask_frozen import Freezer

# from doc_blog

bp = Blueprint('blog', __name__)

speech_client = load_speech_client()

class SearchForm(FlaskForm):
    kudos_start = IntegerField('Kudos', validators=[DataRequired()])
    kudos_end = IntegerField('Kudos End', validators=[DataRequired()])
    fandoms = StringField('Fandoms', validators=[DataRequired()])
    word_count_start = IntegerField('Word Count', validators=[DataRequired()])
    word_count_end = IntegerField('Word Count End', validators=[DataRequired()])
    any_field = StringField('Any Field', validators=[DataRequired()])
    tags = StringField('Tags', validators=[DataRequired()])
    rating = SelectMultipleField('Rating',choices=[('General Audiences', 'General Audiences'),
                                                   ('Teen And Up Audiences', 'Teen And Up Audiences'),
                                                   ('Mature', 'Mature'),
                                                   ('Explicit', 'Explicit')], validate_choice=True)
    submit = SubmitField('Submit')

class ChooseStory(FlaskForm):
    story = SelectField('Story',choices=[], validate_choice=True)
    submit = SubmitField('Submit')
class ChapterForm(FlaskForm):
    chapters = SelectMultipleField('chapters',choices=[], validate_choice=True)
    title = StringField()
    slug = StringField()
    voice = SelectField('Voice',choices=[], validate_choice=True)
    submit = SubmitField('Submit')

class DetailsForm(FlaskForm):
    slug = StringField()
    voice = SelectField('Voice',choices=[], validate_choice=True)
    submit = SubmitField('Submit')


class more_details(FlaskForm):
    slug = StringField()
    voice = SelectField('Voice',choices=[], validate_choice=True)
    submit = SubmitField('Submit')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    slug = db.Column(db.String, unique=True, nullable=False)
    voice = db.Column(db.ForeignKey('voices.id'), nullable=False)
    body = db.Column(db.String)
    audio = db.Column(db.String)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    audio_size = db.Column(db.Integer)

class Voices(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voice_name = db.Column(db.String, unique=True, nullable=False)


@bp.route('/rss.xml')
def rss():
    pass
    # posts = db.session.query(slug, title, voice, body, audio, created, audio_size FROM post p ORDER BY created DESC'
    # ).all()
    # fg = build_rss(posts)
    # return Response(fg.rss_str(), mimetype='application/rss+xml')

@bp.route('/')
def index():

    # db = get_db()
    # posts = db.execute(
    #     'SELECT p.id, slug, voice, body, audio, created, audio_size FROM post p ORDER BY created DESC'
    # ).fetchall()
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
    search_form = SearchForm()


    return render_template('blog/create.html', search_form=search_form)

@bp.route('/keyword_search', methods=('POST',))
def keyword_search():
     search_form = SearchForm()
     if search_form.validate_on_submit():
        kudos_start = search_form.kudos_start.data
        kudos_end = search_form.kudos_end.data
        fandoms = search_form.fandoms.data
        word_count_start = search_form.word_count_start.data
        word_count_end = search_form.word_count_end.data
        any_field = search_form.any_field.data
        tags = search_form.tags.data
        rating = search_form.rating.data
        search = AO3.Search(any_field=any_field, tags=tags,
                            kudos=AO3.utils.Constraint(kudos_start, kudos_end),
                            fandoms=fandoms,
                            word_count=AO3.utils.Constraint(word_count_start, word_count_end),
                            rating=rating)
        search.update()
        choose_story = ChooseStory()
        story_list = []
        for story in search.results:
            story_list.append((story.id, str(f'{story.title} - Kudos: {story.kudos} - rating: {story.rating}')))
        choose_story.story.choices = [story_list]
        search_results = search.results
        return render_template('blog/search_results.html', choose_story=choose_story)


@bp.route('/select_story', methods=('POST',))
def select_story():
        choose_story = ChooseStory()
        story = AO3.Work(choose_story.story.data)
        chapter_form = ChapterForm()
        chapter_form.chapters.choices = [(idx, repr(chapter)) for idx, chapter in enumerate(story.chapters)]
        chapter_form.chapters.choices = db.session.query(Voices).all()
        chapter_form.slug.data = str(f'{story.title}_by_{story.authors[0].username}').replace(",", "").replace(" ", "_")
        sh = shelve.open("work_id")

        return render_template('partials/chapter_results.html', story=story, chapter_form=chapter_form)


@bp.route('/selected_chapters', methods=('POST',))
def selected_chapters():
    sh = shelve.open("file")
    filename = sh['filename']
    chapter_form = ChapterForm()
    segments = chapter_form.chapters.data
    booktitle = chapter_form.title.data
    slug = chapter_form.slug.data
    voice = chapter_form.voice.data
    print(segments)
    book = epub.read_epub(os.path.join(
        current_app.instance_path, 'files', filename
        ))
    items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    for segment in segments:
        ch_content = items[int(segment)].content
        mp3_name = str(f'{slug}-{str(segment)}.mp3')
        title = str(f'{booktitle} - {str(segment)}')
        audio_list = create_mp3(speech_client, ch_content, voice, mp3_name)
        print(audio_list)
        db = get_db()
        result = db.execute(
            'INSERT INTO post (title, slug, body, audio, voice, audio_size )'
            ' VALUES (?, ?, ?, ?, ?, ?)',
            (title, slug, ch_content, audio_list[0], voice, audio_list[1])
        )
        # db.commit()
        # os.system("python freeze.py")
        # os.system("git status")
        # os.system("git add -A")
        # os.system('git commit -m "' + title + '"' )
        # os.system("git push")

    return redirect(url_for('blog.index'))




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

