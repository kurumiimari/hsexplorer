import functools
import gzip

from flask import current_app, request
from flask_redis import FlaskRedis

redis_client = FlaskRedis()


def cacheable_path(invalidator_key=None, timeout=60):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not current_app.config['PERFORM_CACHING']:
                value = func(*args, **kwargs)
                if len(value) == 2:
                    value, code = value
                else:
                    code = 200
                return value, code

            try:
                page = int(request.args.get('page', 1))
            except Exception as e:
                page = 1

            key = 'path:{}:{}'.format(request.path, page)
            if invalidator_key is None:
                key += ':noinv'
            else:
                key += ':{}'.format(invalidator_key())

            cached = redis_client.get(key)
            if cached:
                current_app.logger.debug('Cache hit on {}'.format(key))
                return gzip.decompress(cached).decode('utf-8'), 200

            current_app.logger.debug('Cache miss on {}'.format(key))
            value = func(*args, **kwargs)
            if len(value) == 2:
                value, code = value
            else:
                code = 200
            if code == 200:
                gzipped_value = gzip.compress(value.encode('utf-8'))
                redis_client.setex(key, timeout, gzipped_value)
            return value, code

        return wrapper

    return decorator
