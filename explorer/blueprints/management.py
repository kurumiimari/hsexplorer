import functools

from flask import Blueprint, request, current_app

from explorer.cache import redis_client

management = Blueprint('management', __name__)


def requires_management_key(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        provided_key = request.headers.get('X-Management-Key')
        if provided_key != current_app.config['MANAGEMENT_KEY']:
            return 'Unauthorized', 401

        return func(*args, **kwargs)

    return wrapper


@management.route('/management/flush_cache', methods=('POST',))
@requires_management_key
def flush_cache():
    redis_client.flushall()
    return None, 204
