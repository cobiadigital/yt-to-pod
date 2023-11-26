import os

import keyring
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import requests

db = SQLAlchemy()

if os.getenv('FLASK_SECRET') is None:
    os.environ['FLASK_SECRET'] = keyring.get_password('ytpod', 'flask_secret'),


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("FLASK_SECRET"),
    )


    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///podcast.db"

    app.config['AUDIO_STORE_BASE_URL'] = 'https://yttopod.cobiadigital.com'
    app.config['BASE_URL'] = 'https://yttopod.cobiadigital.com'

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)


    # ensure the instance folder exists
    db_url = 'https://ao3.sobrietytoolkit.com/podcast.db'

    try:
        os.makedirs(app.instance_path)
        req = requests.get(db_url)
        with open(os.path.join(app.instance_path, 'podcast.db'), "wb") as file:
            file.write(req.content)
    except OSError:
        pass

    db.init_app(app)
    # bootstrap.init_app(app)

    @app.cli.command("create-db")
    def create_db():
        db.create_all()
        print("Database created.")

    # with app.app_context():
    #     db.create_all()

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', view_func=blog.index)

    return app

