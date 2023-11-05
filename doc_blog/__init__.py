import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_bootstrap import Bootstrap
# from dotenv import load_dotenv
import requests
# import ssl
# ssl.SSLContext.verify_mode = property(lambda self: ssl.CERT_NONE, lambda self, newval: None)


# load_dotenv()

db = SQLAlchemy()
# bootstrap = Bootstrap()



def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY='1e9a515c032fd01ebd9e4ffGa1f6c27c',
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///podcast.db"

    app.config['AUDIO_STORE_BASE_URL'] = 'https://ao3.sobrietytoolkit.com'
    app.config['BASE_URL'] = 'https://ao3.sobrietytoolkit.com'

    db_url = 'https://ao3.sobrietytoolkit.com/podcast.db'

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

    with app.app_context():
        db.create_all()

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', view_func=blog.index)

    return app

