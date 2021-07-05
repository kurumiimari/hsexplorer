import decimal
import os
from datetime import datetime, timedelta

import idna
from flask import current_app, url_for

from explorer import protocol

current_bundles = None


def scan_bundles():
    global current_bundles
    if current_bundles is not None and not current_app.config['BUNDLES_AUTO_RELOAD']:
        return current_bundles

    current_bundles = {}
    bundle_dir = os.path.join(current_app.static_folder, 'bundles')
    for bname in os.listdir(bundle_dir):
        if not bname.endswith('.bundle.js'):
            continue

        parts = bname.split('.')
        current_bundles[parts[0]] = os.path.join('bundles', bname)


def format_datetime(value, format="%d %b %Y %I:%M %p"):
    if isinstance(value, int):
        value = datetime.fromtimestamp(value)
    if value is None:
        return ''
    return value.strftime(format)


# Taken from https://shubhamjain.co/til/how-to-render-human-readable-time-in-jinja/
def time_ago(timestamp, suffix='ago'):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """

    now = datetime.now()
    timestamp = datetime.fromtimestamp(timestamp) if isinstance(timestamp, int) else timestamp
    future = timestamp > now
    diff = timestamp - now if future else now - timestamp
    second_diff = diff.seconds
    day_diff = diff.days

    out = ''

    if day_diff < 0:
        return out

    if day_diff == 0:
        if second_diff < 10:
            out = 'right now' if future else 'just now'
        elif second_diff < 60:
            out = str(int(second_diff)) + ' seconds'
        elif second_diff < 120:
            out = 'a minute'
        elif second_diff < 3600:
            out = str(int(second_diff / 60)) + ' minutes'
        elif second_diff < 7200:
            out = 'an hour'
        elif second_diff < 86400:
            out = str(int(second_diff / 3600)) + ' hours'
    elif day_diff == 1:
        out = 'Tomorrow' if future else 'Yesterday'
    elif day_diff < 7:
        out = str(day_diff) + ' days'
    elif day_diff < 31:
        out = str(int(day_diff / 7)) + ' weeks'
    elif day_diff < 365:
        out = str(int(day_diff / 30)) + ' months'
    else:
        out = str(int(day_diff / 365)) + ' years'

    return '{}{}'.format(out, ' ' + suffix if suffix else '')


def depunycode(name):
    try:
        return idna.decode(name)
    except Exception as e:
        current_app.logger.error('Error decoding punycode:')
        current_app.logger.exception(e)
        return name


def as_hns(value, include_unit=True):
    if isinstance(value, decimal.Decimal):
        res = value / decimal.Decimal(str(1e6))
    else:
        res = value / 1e6
    res = f'{res:.6f}'
    if include_unit:
        res += ' HNS'
    return res


def middle_ellipsis(value, chars=10):
    if value is None:
        return ''
    if len(value) < chars * 2:
        return value
    return value[:chars] + '...' + value[len(value) - chars:]


def block_count_to_time(blocks):
    days = blocks / protocol.network_main.blocks_per_day
    ts = datetime.now() + timedelta(days=days)
    return time_ago(ts, suffix=None)


def pretty_number(num):
    return '{:,}'.format(num)


_prefixes = (
    ('k', 1e3),  # kilo
    ('M', 1e6),  # mega
    ('G', 1e9),  # giga
    ('T', 1e12),  # tera
    ('P', 1e15),  # peta
    ('E', 1e18),  # exa
    ('Z', 1e21),  # zetta
    ('Y', 1e24),  # yotta
)


def si_units(num, decimals=4):
    pref = ''
    divisor = 1
    for p, d in _prefixes:
        if d > num:
            break

        pref = p
        divisor = d

    return '{:.{decimals}f} {}'.format(float(num) / divisor, pref, decimals=decimals)


def bundle_root(name):
    scan_bundles()
    if name not in current_bundles:
        raise Exception(
            'Bundle not found - please define an entrypoint named "{}" in webpack.config.json.'.format(name)
        )

    out = '<div id="bundle-root-{}"></div>\n'.format(name)
    out += '<script src="{}" type="text/javascript"></script>'.format(url_for('static', filename=current_bundles[name]))
    return out


def register_jinja_helpers(app):
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['time_ago'] = time_ago
    app.jinja_env.filters['depunycode'] = depunycode
    app.jinja_env.filters['as_hns'] = as_hns
    app.jinja_env.filters['middle_ellipsis'] = middle_ellipsis
    app.jinja_env.filters['block_count_to_time'] = block_count_to_time
    app.jinja_env.filters['pretty_number'] = pretty_number
    app.jinja_env.filters['si_units'] = si_units
    app.jinja_env.globals.update(bundle_root=bundle_root)
