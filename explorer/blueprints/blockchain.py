import re

from flask import Blueprint, render_template, request, redirect

from explorer.cache import cacheable_path
from explorer.models import Block, Tx, Name, EntityCounts, PopularNames, PriceTick, Address, MempoolTx, InfoTick
from explorer.protocol import valid_name, validate_address

blockchain = Blueprint('home', __name__)


def invalidate_on_block():
    return Block.max_height()


@blockchain.route('/')
@cacheable_path(invalidate_on_block, timeout=30)
def home_page():
    block_height = Block.max_height()
    txs, _, _ = Tx.all()
    info = InfoTick.latest()
    return render_template(
        'blockchain/home.j2',
        title='Home',
        block_height=block_height,
        latest_price=PriceTick.latest(),
        txs=txs,
        ending_soon=Name.ending_soon(),
        entity_counts=EntityCounts.latest(),
        mempool_count=MempoolTx.count(),
        info=info
    )


@blockchain.route('/blocks')
@cacheable_path(invalidate_on_block, timeout=900)
def blocks_page():
    try:
        page = int(request.args.get('page', 1))
    except Exception as e:
        page = 1

    per_page = 50
    blocks, page_count, result_count = Block.all(page=page, per_page=per_page)
    return render_template(
        'blockchain/blocks.j2',
        title='Blocks',
        blocks=blocks,
        page=page,
        per_page=per_page,
        page_count=page_count,
        result_count=result_count
    )


@blockchain.route('/txs')
@cacheable_path(invalidate_on_block, timeout=900)
def txs_page():
    try:
        page = int(request.args.get('page', 1))
    except Exception as e:
        page = 1

    per_page = 50
    txs, page_count, result_count = Tx.all(page=page, per_page=per_page)
    return render_template(
        'blockchain/txs.j2',
        title='Transactions',
        txs=txs,
        page=page,
        per_page=per_page,
        page_count=page_count,
        result_count=result_count
    )


@blockchain.route('/blockchain')
@cacheable_path(invalidate_on_block, timeout=900)
def blockchain_page():
    blocks, _, _ = Block.all(page=1, per_page=50)
    mempool, _, _ = MempoolTx.all(page=1, per_page=50)
    return render_template(
        'blockchain/blockchain.j2',
        blocks=blocks,
        mempool=mempool
    )


@blockchain.route('/domains')
@cacheable_path(invalidate_on_block, timeout=900)
def domains_page():
    popular_names, _, _ = PopularNames.latest(page=1, per_page=30)
    return render_template(
        'blockchain/domains.j2',
        title='Domains',
        block_height=Block.max_height(),
        ending_soon=Name.ending_soon(),
        popular_names=popular_names,
    )


@blockchain.route('/mempool')
def mempool_page():
    try:
        page = int(request.args.get('page', 1))
    except Exception as e:
        page = 1

    per_page = 50
    mempool, page_count, result_count = MempoolTx.all(page, per_page)
    return render_template(
        'blockchain/mempool.j2',
        title='Mempool',
        mempool=mempool,
        page=page,
        per_page=per_page,
        page_count=page_count,
        result_count=result_count
    )


@blockchain.route('/txs/<tx_hash>')
@cacheable_path()
def tx_page(tx_hash):
    tx = Tx.find_by_hash(tx_hash)
    if tx is None:
        return None, 404

    return render_template(
        'blockchain/tx.j2',
        title='Transaction {}'.format(tx_hash),
        tx=tx
    )


@blockchain.route('/blocks/<int:height>')
@cacheable_path()
def block_by_height_page(height):
    block = Block.find_by_height(height)
    return block_page(block)


@blockchain.route('/blocks/<block_hash>')
@cacheable_path()
def block_by_hash_page(block_hash):
    block = Block.find_by_height(block_hash)
    return block_page(block)


@blockchain.route('/addrs/<address>')
@blockchain.route('/addresses/<address>')
@cacheable_path(invalidate_on_block)
def address_page(address):
    try:
        page = int(request.args.get('page', 1))
    except Exception as e:
        page = 1

    per_page = 50
    addr_obj = Address.find_by_address(address)
    if addr_obj is None:
        return None, 404

    txs, page_count, result_count = Tx.find_by_address(address, page, per_page)
    if result_count == 0:
        return None, 404

    return render_template(
        'blockchain/address.j2',
        title='Address {}'.format(address),
        txs=txs,
        page_count=page_count,
        result_count=result_count,
        per_page=per_page,
        page=page,
        address=addr_obj
    )


@blockchain.route('/names/<name>')
@cacheable_path(invalidate_on_block)
def name_page(name):
    if not valid_name(name):
        return None, 404

    name_info = Name.find_by_name(name, inc_views=True)
    if name_info is None:
        return None, 404

    block_height = Block.max_height()

    if name_info.status['status'] == 'CLOSED':
        return render_template(
            'blockchain/name_closed.j2',
            title='{}/'.format(name),
            name=name_info,
            block_height=block_height
        )

    return render_template(
        'blockchain/name_auction.j2',
        title='{}/'.format(name),
        height=Block.max_height(),
        name=name_info,
    )


@blockchain.route('/search')
def search_page():
    try:
        page = int(request.args.get('page', 1))
    except Exception as e:
        page = 1

    query = request.args.get('query', '')
    if len(query) == 0:
        return redirect('/')

    if re.match('^[a-f0-9]{64}$', query, re.IGNORECASE):
        return redirect('/txs/{}'.format(query))

    if re.match('^[0-9]+$', query):
        return redirect('/blocks/{}'.format(query))

    if validate_address(query):
        return redirect('/addrs/{}'.format(query))

    per_page = 25
    names, page_count, result_count = Name.search_by_name(query, page=page, per_page=per_page)

    return render_template(
        'blockchain/search.j2',
        title='Search',
        names=names,
        page_count=page_count,
        result_count=result_count,
        per_page=per_page,
        page=page,
    ), 200


def block_page(block):
    if block is None:
        return None, 404

    try:
        page = int(request.args.get('page', 1))
    except Exception as e:
        page = 1

    per_page = 50
    txs, page_count, result_count = Tx.find_by_block_height(block.height, page=page, per_page=per_page)
    return render_template(
        'blockchain/block.j2',
        title='Block {}'.format(block.height),
        block=block,
        txs=txs,
        page_count=page_count,
        result_count=result_count,
        per_page=per_page,
        page=page
    )
