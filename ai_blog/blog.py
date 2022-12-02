from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from ai_blog.db import get_db

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from flask_ckeditor import CKEditor, CKEditorField

from ai_blog.tts import create_mp3

bp = Blueprint('blog', __name__)

class PostForm(FlaskForm):
    title = StringField('Title')
    slug = StringField('Slug')
    body = CKEditorField('Body', validators=[DataRequired()])
    voice = StringField('Voice')
    submit = SubmitField('Submit')

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created FROM post p ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
def create():
    form = PostForm()
    if request.method == 'POST':
        title = form.title.data
        slug = form.slug.data
        body = form.body.data
        voice = form.voice.data
        error = None

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
            audio = create_mp3(id, slug, body, voice)
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