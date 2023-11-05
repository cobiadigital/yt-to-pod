#Load Flask modules
from flask import (
    Blueprint, flash, g, redirect, Response, render_template, request, url_for, send_from_directory,
    current_app, send_file
)

import logging
import boto3
from botocore.exceptions import ClientError

from .models import Post, Voices

#Load 3rd Party
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, IntegerField, RadioField, HiddenField
from wtforms.validators import DataRequired

#Load app functions
from . import db
from .rss import build_rss
#import requests
import io
# from flask_frozen import Freezer

# from doc_blog

bp = Blueprint('blog', __name__)

search = None


class GetUrlForm(FlaskForm):
    get_url = StringField('URL of Youtube Video or Playlist')
    submit = SubmitField('Submit')

class ChooseItem(FlaskForm):
    story = RadioField('Story', choices=[])
    submit = SubmitField('Submit')
class ChapterForm(FlaskForm):
    chapters = SelectMultipleField('chapters', choices=[], validate_choice=True)
    title = StringField()
    slug = StringField()
    voice = SelectField('Voice',choices=[], validate_choice=True)
    story = HiddenField()
    submit = SubmitField('Submit')


class DetailsForm(FlaskForm):
    slug = StringField()
    voice = SelectField('Voice',choices=[], validate_choice=True)
    submit = SubmitField('Submit')


class more_details(FlaskForm):
    slug = StringField()
    voice = SelectField('Voice',choices=[], validate_choice=True)
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

@bp.route('/url_results', methods=('POST',))
def url_results():
    # rating = search_form.rating.data
    get_url_form = GetUrlForm()
    selected_url = get_url_form.get_url.data

    return render_template('partials/url_results.html', selected_url=selected_url)



@bp.route('/next_page', methods=('POST',))
def next_page():
    global search
    search.page += 1
    search.update()
    choose_story = ChooseStory()
    story_list = []
    for story in search.results:
        story_list.append((story.id, str(f'{story.title} - Kudos: {story.kudos}')))
    if len(story_list) == 0:
        story_list.append((0, 'No results found'))
    choose_story.story.choices = story_list
    return render_template('partials/url_results.html', choose_story=choose_story,
                           page=search.page,
                           pages=search.pages
                           )


@bp.route('/select_story', methods=('POST',))
def select_story():
    choose_story = ChooseStory()
    g.story = AO3.Work(choose_story.story.data)
    chapter_form = ChapterForm()
    chapter_form.chapters.choices = [(idx, repr(chapter)) for idx, chapter in enumerate(g.story.chapters)]
    chapter_form.voice.choices = get_voices(speech_client)
    chapter_form.voice.data = ('en-US-SaraNeural', 'en-US-SaraNeural')
    chapter_form.slug.data = str(f'{g.story.title}_by_{g.story.authors[0].username}').replace(",", "").replace(" ", "_").replace("?", "")
    chapter_form.title.data = str(f'{g.story.title} by {g.story.authors[0].username}')
    chapter_form.story.data = g.story.id
    return render_template('partials/chapter_results.html',
                           metadata=g.story.metadata,
                           chapter_form=chapter_form)
@bp.route('/selected_chapters', methods=('POST',))
def selected_chapters():
    chapter_form = ChapterForm()
    segments = chapter_form.chapters.data
    work_title = chapter_form.title.data
    slug = chapter_form.slug.data
    voice = chapter_form.voice.data
    story_id = chapter_form.story.data
    work = AO3.Work(story_id)
    for segment in segments:
        # ch_content = work.chapters[int(segment)]._soup
        ch_content = work.chapters[int(segment)].text
        mp3_name = str(f'{slug}-{str(segment)}.mp3')
        title = str(f'{work_title} - {str(segment)}')
        summary = str(f'{work.summary} \n\n <h3>Chapter Summary</h3><p> {work.chapters[int(segment)].summary}</p>')
        audio_list = create_mp3(speech_client, ch_content, voice, mp3_name)
        db.session.add(Post(title=title, slug=slug, voice=voice, body=summary, audio=audio_list[0], audio_size=audio_list[1]))
        db.session.commit()
        db_name = 'podcast.db'
        db_path = os.path.join(current_app.instance_path, db_name)
        rss_name = 'rss.xml'
        s3 = get_s3client()
        bucket = 'archive'

        try:
            response = s3.upload_file(db_path, bucket, db_name)
        except ClientError as e:
             print(e)
        try:
            url = current_app.url_for('blog.rss')
            req = requests.get(url)
            rss_file = io.BytesIO(req.content)
            response = s3.upload_fileobj(rss_file, bucket, rss_name)
        except ClientError as e:
            print(e)

        return redirect(url_for('blog.index'))


        # os.system("python freeze.py")
        # os.system("git status")
        # os.system("git add -A")
        # os.system('git commit -m "' + title + '"' )
        # os.system("git push")

    return redirect(url_for('blog.index'))




def get_post(id):
    post = db.first_or_404(Post, id=id)

    return post

@bp.route('/<int:id>/', methods=('GET',))
def post_page(id):
    post = get_post(id)
    audio_store_url = current_app.config.get_namespace('AUDIO_STORE_URL')

    return render_template('blog/post_page.html', post=post, audio_store_url=audio_store_url)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
def update(id):
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

