import binascii

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, distinct
from sqlalchemy.dialects.postgresql import JSONB

from explorer import protocol
from explorer.protocol import parse_address, parse_name_resource

db = SQLAlchemy()


class Block(db.Model):
    __tablename__ = 'blocks'

    height = db.Column(db.Integer, primary_key=True)
    hash = db.Column(db.String(64), nullable=False, index=True, unique=True)
    prev_hash = db.Column(db.String(64), nullable=False)
    merkle_root = db.Column(db.String(64), nullable=False)
    witness_root = db.Column(db.String(64), nullable=False)
    tree_root = db.Column(db.String(64), nullable=False)
    reserved_root = db.Column(db.String(64), nullable=False)
    time = db.Column(db.Integer, nullable=False)
    bits = db.Column(db.Integer, nullable=False)
    nonce = db.Column(db.BigInteger, nullable=False)
    extra_nonce = db.Column(db.String, nullable=False)
    mask = db.Column(db.String, nullable=False)

    txs = db.relationship('Tx', back_populates='block')

    @property
    def coinbase(self):
        return Output.query.join(Tx) \
            .filter(Tx.block_height == self.height) \
            .filter(Tx.index == 0) \
            .filter(Output.index == 0) \
            .first()

    @property
    def coinbase_value(self):
        return db.session.query(func.sum(Output.value)) \
            .join(Tx) \
            .filter(Output.block_height == self.height) \
            .filter(Output.covenant_action == 'NONE') \
            .filter(Tx.index == 0) \
            .first()[0]

    @property
    def tx_count(self):
        return db.session.query(func.count(Tx.id)) \
            .filter(Tx.block_height == self.height) \
            .first()[0]

    @classmethod
    def find_by_height(cls, height):
        return cls.query.filter_by(height=height).first()

    @classmethod
    def max_height(cls):
        return db.session.query(func.coalesce(func.max(Block.height), 0)).first()[0]

    @classmethod
    def all(cls, page=1, per_page=25):
        return pageable(cls.query, page, per_page, order_by=(cls.height.desc(),))


class Tx(db.Model):
    __tablename__ = 'txs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    block_height = db.Column(db.Integer, db.ForeignKey('blocks.height'), nullable=False, index=True)
    hash = db.Column(db.String(64), nullable=False, unique=True)
    witness_hash = db.Column(db.String(64), nullable=False)
    fee = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Integer, nullable=False)
    mtime = db.Column(db.Integer, nullable=False, index=True)
    index = db.Column(db.Integer, nullable=False)
    version = db.Column(db.Integer, nullable=False)
    locktime = db.Column(db.Integer, nullable=False)
    hex = db.Column(db.Text, nullable=False)

    block = db.relationship('Block', back_populates='txs', foreign_keys=[block_height])
    inputs = db.relationship('Input', back_populates='tx')
    outputs = db.relationship('Output', back_populates='tx')

    @property
    def output_amount(self):
        return db.session.query(func.sum(Output.value), Output.tx_hash) \
            .filter(Output.tx_hash == self.hash) \
            .group_by(Output.tx_hash) \
            .first()[0]

    @classmethod
    def find_by_hash(cls, h):
        return cls.query.filter_by(hash=h).first()

    @classmethod
    def all(cls, page=1, per_page=25):
        return pageable(cls.query, page, per_page,
                        order_by=(cls.id.desc(),),
                        count_override=EntityCounts.latest().txs)

    @classmethod
    def find_by_block_height(cls, block_height, page, per_page):
        q = cls.query.filter_by(block_height=block_height)
        return pageable(q, page, per_page, order_by=(cls.index.asc(),))

    @classmethod
    def find_by_address(cls, address, page, per_page):
        inputs = cls.query.join(Input, Input.tx_hash == Tx.hash) \
            .filter(Input.prevout_address == address)
        outputs = cls.query.join(Output, Output.tx_hash == Tx.hash) \
            .filter(Output.address == address)
        q = inputs.union(outputs)

        return pageable(q, page, per_page,
                        order_by=(cls.block_height.desc(), cls.index.desc()),
                        count_override=Address.tx_count_by_address(address))


class Output(db.Model):
    __tablename__ = 'outputs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    block_height = db.Column(db.Integer, db.ForeignKey('blocks.height'), nullable=False, index=True)
    tx_hash = db.Column(db.String(64), db.ForeignKey('txs.hash'), nullable=False, index=True)
    index = db.Column(db.Integer, nullable=False, index=True)
    value = db.Column(db.BigInteger, nullable=False)
    address = db.Column(db.String, nullable=False, index=True)
    covenant_type = db.Column(db.Integer, nullable=False)
    covenant_action = db.Column(db.String, nullable=False, index=True)
    covenant_items = db.Column(JSONB, nullable=False)
    covenant_name_hash = db.Column(db.String, db.ForeignKey('names.hash'), nullable=True, index=True)

    block = db.relationship('Block', foreign_keys=[block_height])
    tx = db.relationship('Tx', back_populates='outputs', foreign_keys=[tx_hash])
    name = db.relationship('Name', foreign_keys=[covenant_name_hash])

    __table_args__ = (
        db.UniqueConstraint(tx_hash, index),
    )

    @property
    def transfer_address(self):
        if self.covenant_action != 'TRANSFER':
            return None

        return parse_address(self.covenant_items[2], self.covenant_items[3])

    @property
    def name_hash(self):
        if self.covenant_action == 'NONE':
            return None
        return self.covenant_items[0]

    @property
    def corresponding_reveal(self):
        if self.covenant_action != 'BID':
            return None

        return Output.query.filter_by(covenant_action='REVEAL') \
            .filter_by(address=self.address) \
            .filter_by(covenant_name_hash=self.covenant_name_hash) \
            .order_by(Output.id) \
            .first()


class Input(db.Model):
    __tablename__ = 'inputs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tx_hash = db.Column(db.String(64), db.ForeignKey('txs.hash'), nullable=False, index=True)
    index = db.Column(db.BigInteger, nullable=False)
    prevout_hash = db.Column(db.String(64), nullable=True)
    prevout_index = db.Column(db.Integer, nullable=True)
    prevout_address = db.Column(db.String, nullable=True, index=True)
    coinbase = db.Column(db.Boolean, nullable=False)

    tx = db.relationship('Tx', back_populates='inputs', foreign_keys=[tx_hash])
    prevout = db.relationship('Output', foreign_keys=[prevout_hash, prevout_index])

    __table_args__ = (
        db.ForeignKeyConstraint([prevout_hash, prevout_index], [Output.tx_hash, Output.index]),
    )


class Name(db.Model):
    __tablename__ = 'names'

    name = db.Column(db.String(64), primary_key=True)
    hash = db.Column(db.String(64), nullable=False, unique=True)
    views = db.Column(db.Integer, nullable=False, server_default='0')

    @property
    def outputs(self):
        return Output.query.join(Tx) \
            .filter(Output.covenant_name_hash == self.hash) \
            .order_by(Tx.mtime.desc())

    @property
    def highest_lockup(self):
        return db.session.query(func.coalesce(func.max(Output.value), 0)) \
            .filter(Output.covenant_action == 'BID') \
            .filter(Output.covenant_name_hash == self.hash) \
            .first()[0]

    @property
    def highest_bid(self):
        return db.session.query(func.coalesce(func.max(Output.value), 0)) \
            .filter(Output.covenant_action == 'REVEAL') \
            .filter(Output.covenant_name_hash == self.hash) \
            .first()[0]

    @property
    def price_paid(self):
        q = db.session.query(Output.value) \
            .filter(Output.covenant_action == 'REVEAL') \
            .filter(Output.covenant_name_hash == self.hash) \
            .order_by(Output.value.desc())

        second_highest = q.offset(1).first()
        return 0 if second_highest is None else second_highest[0]

    @property
    def total_bids(self):
        return Output.query.filter_by(covenant_action='BID') \
            .filter_by(covenant_name_hash=self.hash) \
            .count()

    @property
    def renewal_height(self):
        out = Output.query.filter(Output.covenant_action.in_(('REGISTER', 'RENEW'))) \
            .filter(Output.covenant_name_hash == self.hash) \
            .order_by(Output.id.desc()) \
            .first()

        return out.tx.block_height + protocol.network_main.renewal_window

    @property
    def records(self):
        out = Output.query.filter(Output.covenant_action.in_(('REGISTER', 'UPDATE'))) \
            .filter(Output.covenant_name_hash == self.hash) \
            .order_by(Output.id.desc()) \
            .first()

        if out is None:
            return parse_name_resource(None)

        resource_hex = out.covenant_items[2]
        packet = binascii.unhexlify(resource_hex)
        return parse_name_resource(packet)

    @property
    def status(self):
        state = {}
        block_height = Block.max_height()

        open_sc = db.session.query(Output) \
            .filter(Output.covenant_action == 'OPEN') \
            .filter(Output.covenant_name_hash == self.hash) \
            .order_by(Output.id.desc()) \
            .first()

        if open_sc is None:
            claim_sc = db.session.query(Output) \
                .filter(Output.covenant_action == 'CLAIM') \
                .filter(Output.covenant_name_hash == self.hash) \
                .order_by(Output.id.desc()) \
                .first()

            if claim_sc is None:
                state['status'] = 'UNKNOWN'
            else:
                state['status'] = 'CLOSED'

            return state

        state['open_height'] = open_sc.tx.block.height
        if block_height <= state['open_height'] + protocol.network_main.open_period:
            state['status'] = 'OPENING'
            return state

        bidding_period_end = state['open_height'] + \
                             protocol.network_main.open_period + \
                             protocol.network_main.bidding_period + 1
        state['bidding_period_end'] = bidding_period_end
        if bidding_period_end > block_height:
            state['status'] = 'BIDDING'
            return state

        reveal_period_end = bidding_period_end + protocol.network_main.reveal_period
        state['reveal_period_end'] = reveal_period_end
        if reveal_period_end > block_height:
            state['status'] = 'REVEALING'
            return state

        state['status'] = 'CLOSED'
        return state

    @classmethod
    def find_by_name(cls, name, inc_views=True):
        out = cls.query.filter_by(name=name).first()
        if out is None:
            return None
        if inc_views:
            out.views += 1
        db.session.commit()
        return out

    @classmethod
    def ending_soon(cls):
        # ending in 6 hours
        lo = Block.max_height() - protocol.network_main.bidding_period - protocol.network_main.open_period + 1
        hi = lo + 36
        opens = db.session.query(Output.covenant_name_hash) \
            .filter(Output.block_height > lo) \
            .filter(Output.block_height <= hi) \
            .filter(Output.covenant_action == 'OPEN') \
            .order_by(Output.block_height.asc()) \
            .limit(30) \
            .subquery()

        return cls.query.filter(cls.hash.in_(opens))

    @classmethod
    def search_by_name(cls, name, page, per_page):
        q = cls.query.filter(Name.name.ilike('%{}%'.format(name)))
        return pageable(q, page, per_page, order_by=(cls.name.asc(),))


class EntityCounts(db.Model):
    __tablename__ = 'entity_counts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    opened_names = db.Column(db.Integer, nullable=False, server_default='0')
    txs = db.Column(db.Integer, nullable=False, server_default='0')

    @classmethod
    def latest(cls):
        return cls.query.filter_by(id=1).first()


class PopularNames(Name):
    __tablename__ = 'popular_names'

    __mapper_args__ = {
        'concrete': True
    }

    name = db.Column(db.String(64), primary_key=True)
    hash = db.Column(db.String(64), nullable=False, unique=True)
    views = db.Column(db.Integer, nullable=False, server_default='0')
    bid_count = db.Column(db.Integer, nullable=False, server_default='0')
    last_bid_height = db.Column(db.Integer, nullable=False, server_default='0')
    last_bid_time = db.Column(db.Integer, nullable=False, server_default='0')

    @classmethod
    def latest(cls, page, per_page):
        order_by = (cls.bid_count.desc(), cls.views.desc(), cls.last_bid_time.desc())
        return pageable(cls.query, page, per_page, order_by=order_by)


class Address(db.Model):
    __tablename__ = 'addresses'

    address = db.Column(db.String, primary_key=True)
    tx_count = db.Column(db.Integer, nullable=False, server_default='0')
    received = db.Column(db.BigInteger, nullable=False, server_default='0')
    spent = db.Column(db.BigInteger, nullable=False, server_default='0')

    @property
    def total_received(self):
        results = db.session.query(func.coalesce(func.sum(Output.value), 0)) \
            .filter(Output.address == self.address) \
            .first()

        return results[0]

    @property
    def total_spent(self):
        results = db.session.query(func.coalesce(func.sum(distinct(Output.value)), 0)) \
            .select_from(Input) \
            .join(Output, Output.address == Input.prevout_address) \
            .filter(Input.prevout_address == self.address) \
            .first()

        return results[0]

    @property
    def balance(self):
        return self.total_received - self.total_spent

    @classmethod
    def find_by_address(cls, address):
        return cls.query.filter_by(address=address).first()

    @classmethod
    def tx_count_by_address(cls, address):
        addr = cls.find_by_address(address)
        if addr is None:
            return 0
        return addr.tx_count


class PriceTick(db.Model):
    __tablename__ = 'price_ticks'

    id = db.Column(db.Integer, primary_key=True)
    price_usd = db.Column(db.BigInteger, nullable=False)
    market_cap_usd = db.Column(db.BigInteger, nullable=False)
    created_at = db.Column(db.Integer, nullable=False)

    @classmethod
    def latest(cls):
        return cls.query.order_by(cls.id.desc()).first()


class MempoolTx(db.Model):
    __tablename__ = 'mempool_txs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    first_seen = db.Column(db.Integer, nullable=False)
    aggregate_value = db.Column(db.BigInteger, nullable=False)
    fee = db.Column(db.BigInteger, nullable=False)

    @classmethod
    def all(cls, page, per_page):
        return pageable(cls.query, page, per_page, order_by=(cls.first_seen.desc(),))

    @classmethod
    def count(cls):
        return cls.query.count()


class InfoTick(db.Model):
    __tablename__ = 'info_ticks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hashrate = db.Column(db.Numeric(32, 8), nullable=False)
    difficulty = db.Column(db.Numeric(32, 8), nullable=False)
    created_at = db.Column(db.Integer, nullable=False)

    @classmethod
    def latest(cls):
        return cls.query.order_by(cls.id.desc()).first()


def pageable(query, page, per_page, order_by=None, count_override=None):
    if count_override:
        result_count = count_override
    else:
        result_count = query.count()
    page_count = int(result_count / per_page) + 1

    results = query
    if order_by is not None:
        for o in order_by:
            results = results.order_by(o)

    results = results.offset((page - 1) * per_page) \
        .limit(per_page)
    return results, page_count, result_count
