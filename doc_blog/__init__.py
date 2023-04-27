import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap


db = SQLAlchemy()
bootstrap = Bootstrap()



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///podcast.db"

    app.config['AUDIO_STORE_BASE_URL'] = 'https://ao3.sobrietytoolkit.com'
    app.config['BASE_URL'] = 'https://ao3.sobrietytoolkit.com'

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    db.init_app(app)
    bootstrap.init_app(app)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', view_func=blog.index)

    return app

