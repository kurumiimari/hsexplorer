import signal
import sys
import time

import requests
from flask import current_app

from explorer import protocol
from explorer.cache import redis_client
from explorer.hsd_client import node_rpc_client, node_client
from explorer.models import Block, db, Tx, Input, Output, Name, PriceTick, MempoolTx, InfoTick, EntityCounts, Address

ZERO_HASH = '0000000000000000000000000000000000000000000000000000000000000000'


def lock_block_indexer():
    now = int(time.time())
    new_timeout = now + 3600
    acquired = redis_client.setnx('lock.indexer', str(new_timeout))
    if acquired == 1:
        return True

    existing_timeout = int(redis_client.get('lock.indexer').decode('utf-8'))
    if now > existing_timeout:
        current_app.logger.warn('Deadlock detected.')
        existing_timeout = int(redis_client.getset('lock.indexer', new_timeout).decode('utf-8'))
        return int(existing_timeout) < now

    return False


def index_blocks():
    current_app.logger.info('Started indexer.')
    lock_active = False

    def cleanup(sig, frame):
        if lock_active:
            redis_client.delete('lock.indexer')
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    while True:
        if not lock_block_indexer():
            current_app.logger.info('Indexer is locked, sleeping.')
            time.sleep(60)
            continue

        lock_active = True

        try:
            indexed_height = Block.max_height()
            chain_height = node_client.get_server_info()['chain']['height']
            new_height = indexed_height
            current_app.logger.info('Current height: {}, chain height: {}'.format(indexed_height, chain_height))
            stop_height = indexed_height + 1 + 100
            if stop_height > chain_height + 1:
                stop_height = chain_height + 1
            for height in range(indexed_height + 1, stop_height):
                index_block(height)
                new_height = height

            db.session.execute('SELECT refresh_popular_names(:min_height)', {
                'min_height': new_height - protocol.network_main.bidding_period - protocol.network_main.open_period
            })
            db.session.commit()
        except Exception as e:
            current_app.logger.error('Error while indexing:')
            current_app.logger.exception(e)
        finally:
            redis_client.delete('lock.indexer')
            lock_active = False
        current_app.logger.info('Indexing done, sleeping.')
        time.sleep(60)


def index_ticks():
    try:
        index_price()
    except Exception as e:
        current_app.logger.error('Error indexing price tick:')
        current_app.logger.exception(e)

    try:
        index_info()
    except Exception as e:
        current_app.logger.error('Error indexing info tick:')
        current_app.logger.exception(e)

    current_app.logger.info('Done indexing ticks.')


def index_price():
    url = 'https://api.coingecko.com/api/v3/coins/handshake'
    res = requests.get(url, headers={
        'Accept': 'application/json'
    })
    res.raise_for_status()
    res_json = res.json()

    pt = PriceTick(
        price_usd=int(res_json['market_data']['current_price']['usd'] * 1000000),
        market_cap_usd=int(res_json['market_data']['market_cap']['usd']),
        created_at=int(time.time())
    )
    db.session.add(pt)
    db.session.commit()


def index_info():
    info = node_rpc_client.get_info()
    hashrate = node_rpc_client.get_network_hash_ps(height=Block.max_height())

    it = InfoTick(
        difficulty=info['difficulty'],
        hashrate=hashrate,
        created_at=int(time.time())
    )
    db.session.add(it)
    db.session.commit()


def index_block(height):
    entity_counts = EntityCounts.latest()
    block_json = node_client.get_block(height)
    block = Block(
        height=height,
        hash=block_json['hash'],
        prev_hash=block_json['prevBlock'],
        merkle_root=block_json['merkleRoot'],
        witness_root=block_json['witnessRoot'],
        tree_root=block_json['treeRoot'],
        reserved_root=block_json['reservedRoot'],
        time=block_json['time'],
        bits=block_json['bits'],
        nonce=block_json['nonce'],
        extra_nonce=block_json['extraNonce'],
        mask=block_json['mask']
    )
    db.session.add(block)

    for tx_json in block_json['txs']:
        entity_counts.txs += 1
        tx = Tx(
            hash=tx_json['hash'],
            witness_hash=tx_json['witnessHash'],
            fee=tx_json['fee'],
            rate=tx_json['rate'],
            mtime=tx_json['mtime'],
            index=tx_json['index'],
            version=tx_json['version'],
            locktime=tx_json['locktime'],
            hex=tx_json['hex']
        )
        block.txs.append(tx)
        for i, in_json in enumerate(tx_json['inputs']):
            coinbase = in_json['prevout']['hash'] == ZERO_HASH

            inp = Input(
                index=i,
                prevout_hash=in_json['prevout']['hash'] if not coinbase else None,
                prevout_index=in_json['prevout']['index'] if not coinbase else None,
                prevout_address=in_json['coin']['address'] if not coinbase else None,
                coinbase=coinbase
            )
            tx.inputs.append(inp)

        distinct_addresses = set()
        for i, out_json in enumerate(tx_json['outputs']):
            cov_name_hash = out_json['covenant']['items'][0] if out_json['covenant']['action'] != 'NONE' else None
            out = Output(
                block=block,
                index=i,
                value=out_json['value'],
                address=out_json['address'],
                covenant_type=out_json['covenant']['type'],
                covenant_action=out_json['covenant']['action'],
                covenant_items=out_json['covenant']['items'],
                covenant_name_hash=cov_name_hash
            )

            if out_json['address'] not in distinct_addresses:
                address = Address.find_by_address(out_json['address'])
                if address is None:
                    address = Address(
                        address=out_json['address'],
                        tx_count=0
                    )
                    db.session.add(address)
                address.tx_count += 1

            if out.covenant_action == 'OPEN':
                entity_counts.opened_names += 1
                index_open(out)
            elif out.covenant_action == 'CLAIM':
                index_claim(out)
            tx.outputs.append(out)

    db.session.commit()
    current_app.logger.info('Indexed block {}'.format(height))


def index_open(out):
    name = bytes.fromhex(out.covenant_items[2]).decode('utf-8')
    stored_name = Name.find_by_name(name)
    if stored_name is None:
        db.session.add(Name(
            hash=out.covenant_items[0],
            name=name
        ))


def index_claim(out):
    name = bytes.fromhex(out.covenant_items[2]).decode('utf-8')
    # there can be duplicate name claims now
    existing_name = Name.find_by_name(name, False)
    if existing_name is not None:
        return
    db.session.add(Name(
        hash=out.covenant_items[0],
        name=name
    ))


def index_mempool():
    raw_mp = node_rpc_client.get_raw_mempool(verbose=True)
    hashes = raw_mp.keys()
    to_delete = []

    for txh in hashes:
        try:
            node_tx = node_client.get_tx_by_hash(txh)
        except Exception as e:
            current_app.logger.error('Error retrieving transaction:')
            current_app.logger.exception(e)
            to_delete.append(txh)
            continue

        db_tx = MempoolTx.query.filter_by(hash=txh).first()
        if db_tx is None:
            db_tx = MempoolTx(
                hash=txh,
                first_seen=int(time.time()),
            )
            db.session.add(db_tx)
        values = [0 if o['covenant']['action'] == 'BID' else o['value'] for o in node_tx['outputs']]
        db_tx.aggregate_value = sum(values)
        db_tx.fee = node_tx['fee']

    MempoolTx.query.filter(MempoolTx.hash.notin_(hashes) | MempoolTx.hash.in_(to_delete)).delete()
    db.session.commit()

    current_app.logger.info('Successfully indexed mempool.')
