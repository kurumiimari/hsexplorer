import os
from logging.config import dictConfig

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from explorer.app import create_app
from explorer.indexer import index_ticks, index_mempool, index_blocks
from explorer.models import db

stream_handler = {
    'class': 'logging.StreamHandler',
    'stream': 'ext://sys.stdout',
    'formatter': 'default'
}

if 'LOG_FILE' in os.environ:
    stream_handler = {
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': '/var/log/{}/{}.log'.format(os.environ['LOG_DIR'], os.environ['LOG_FILE']),
        'formatter': 'default',
        'maxBytes': 10485760,
        'backupCount': 3,
    }

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'default': stream_handler
    },
    'root': {
        'level': 'INFO',
        'handlers': ['default']
    }
})

app = create_app()
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)


@manager.command
def run_block_indexer():
    index_blocks()


@manager.command
def run_tick_indexer():
    index_ticks()


@manager.command
def run_mempool_indexer():
    index_mempool()


if __name__ == '__main__':
    manager.run()
