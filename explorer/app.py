import os

from flask import Flask, render_template

from explorer.blueprints.blockchain import blockchain
from explorer.blueprints.management import management
from explorer.cache import redis_client
from explorer.hsd_client import node_rpc_client, node_client
from explorer.jinja_helpers import register_jinja_helpers
from explorer.models import db


def create_app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql://localhost:5432/hsexplorer'),
        SQLALCHEMY_ECHO=os.getenv('SQLALCHEMY_ECHO', '') == '1',
        SECRET_KEY=os.getenv('SECRET_KEY', ''),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        HSD_HOST=os.getenv('HSD_HOST', 'http://localhost:12037'),
        HSD_API_KEY=os.getenv('HSD_API_KEY', None),
        TEMPLATES_AUTO_RELOAD=os.getenv('FLASK_ENV', '') == 'development',
        BUNDLES_AUTO_RELOAD=os.getenv('FLASK_ENV', '') == 'development',
        PERFORM_CACHING=os.getenv('FLASK_ENV', '') != 'development',
        REDIS_URL=os.getenv('REDIS_URL', 'redis://localhost:6379'),
        MANAGEMENT_KEY=os.getenv('MANAGEMENT_KEY', '')
    )

    @app.after_request
    def add_header(response):
        if not app.config['PERFORM_CACHING']:
            response.cache_control.no_store = True
        return response

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.j2'), 404

    db.init_app(app)
    redis_client.init_app(app)
    node_rpc_client.init_app(app)
    node_client.init_app(app)
    app.register_blueprint(blockchain)
    app.register_blueprint(management)
    register_jinja_helpers(app)

    return app
