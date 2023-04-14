#Load Flask modules
from flask import (
    Blueprint, flash, g, redirect, Response, render_template, request, url_for, send_from_directory,
    current_app, send_file
)
from werkzeug.exceptions import abort
import os
from doc_blog.tts import create_mp3

#Load 3rd Party
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, SelectMultipleField
from flask_wtf.file import FileField, FileRequired
from wtforms.validators import DataRequired
from flask_ckeditor import CKEditor, CKEditorField
from feedgen.feed import FeedGenerator
from werkzeug.utils import secure_filename
import ebooklib
from ebooklib import epub
import shelve

#needs a running tika server using java -jar tika-server-1.24.jar
from tika import parser

#Load app functions
from doc_blog.db import get_db
from doc_blog.tts import create_mp3, synthesize_ssml
from doc_blog.tts_voices import get_voices
from doc_blog.load_azure_client import load_speech_client, get_keys
from doc_blog.rss import build_rss
from flask_frozen import Freezer

# from doc_blog

bp = Blueprint('blog', __name__)

speech_client = load_speech_client()

class UploadForm(FlaskForm):
    file = FileField()
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


class upload_file(FlaskForm):
    file = FileField(validators=[FileRequired()])

class more_details(FlaskForm):
    slug = StringField()
    voice = SelectField('Voice',choices=[], validate_choice=True)
    submit = SubmitField('Submit')



@bp.route('/rss.xml')
def rss():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, slug, title, voice, body, audio, created, audio_size FROM post p ORDER BY created DESC'
    ).fetchall()
    fg = build_rss(posts)
    return Response(fg.rss_str(), mimetype='application/rss+xml')

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, slug, voice, body, audio, created, audio_size FROM post p ORDER BY created DESC'
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
    upload_form = UploadForm()
    if request.method == 'POST':
        sh = shelve.open("file")
        sh.close()
        print(form.file.data.filename)
        if form.file.data:
            sh['filename'] = form.file.data.filename
            f = form.file.data
            f.save(os.path.join(
                current_app.instance_path, 'files', sh['filename']
                ))
#             file_data = form.file.data.read()
        voice = form.voice.data
        error = None
        split_tup = os.path.splitext(filename)
        file_name = split_tup[0]
        file_ext = split_tup[1]

        if file_ext == '.pdf':
            pdf_parsed = parser.from_file(file_data, xmlContent=True)
            pdf_content = pdf_parsed["content"]
        elif file_ext == '.epub':
            book = epub.read_epub(os.path.join(
                current_app.instance_path, 'files', sh['filename']
                ))
            items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            n = 0
            chapters_list =[]
            for item in items:
                chapters_list.append((n, item.get_name()))
                n += 1
            chapter_form = ChapterForm()
            chapter_form.chapters.choices = chapters_list
            return render_template('blog/ebook.html', chapter_form=chapter_form)
        else:
            print('neither pdf or epub')


    return render_template('blog/create.html', upload_form=upload_form)

@bp.route('/upload_file', methods=('GET','POST'))
def upload_file():
    if request.method == 'GET':
         return redirect(url_for('blog.index'))
    if request.method == 'POST':
        upload_form = UploadForm()
        sh = shelve.open("file")
        if upload_form.file.data:
            filename = upload_form.file.data.filename
            sh['filename'] = filename
            f = upload_form.file.data
            f.save(os.path.join(
                current_app.instance_path, 'files', filename
                ))
    #             file_data = form.file.data.read()
        error = None
        split_tup = os.path.splitext(sh['filename'])
        file_name = split_tup[0]
        file_ext = split_tup[1]

        if file_ext == '.pdf':
            pdf_parsed = parser.from_file(file_data, xmlContent=True)
            pdf_content = pdf_parsed["content"]
        elif file_ext == '.epub':
            book = epub.read_epub(os.path.join(
                current_app.instance_path, 'files', filename
                ))
            items = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
            n = 0
            chapters_list =[]
            for item in items:
                chapters_list.append((n, str(f'{item.get_name()} - {len(item.get_content())}')))
                n += 1
            chapter_form = ChapterForm()
            chapter_form.title.data = book.title
            chapter_form.chapters.choices = chapters_list
            chapter_form.slug.data = book.title.replace(",","").replace(" ","_")
            db = get_db()
            voice_list = db.execute('SELECT * FROM voices;').fetchall()
            chapter_form.voice.choices = [(voice[0],voice[1]) for voice in voice_list]
    #         form.voice.data = defaults['voice']

            return render_template('partials/chapters.html', chapter_form=chapter_form)

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
        db.commit()
        os.system("python freeze.py")
        os.system("git status")
        os.system("git add -A")
        os.system('git commit -m "' + title + '"' )
        os.system("git push")

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

