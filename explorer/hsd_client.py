import requests


class ClientError(Exception):
    pass


class RPCError(ClientError):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code

    def __str__(self):
        return 'Error {}: {}'.format(self.code, super().__str__())


class BaseClient:
    def __init__(self, url, api_key):
        self.url = url
        self.api_key = api_key
        self.sess = requests.Session()

    def post_json(self, path, body):
        self.prepare(path, 'POST', body)
        res = self.sess.post(url=self.full_url(path), json=body, auth=('x', self.api_key) if self.api_key else None)
        res.raise_for_status()
        return res.json()

    def put_json(self, path, body):
        self.prepare(path, 'PUT', body)
        res = self.sess.put(url=self.full_url(path), json=body, auth=('x', self.api_key) if self.api_key else None)
        res.raise_for_status()
        return res.json()

    def get_json(self, path):
        self.prepare(path, 'GET', None)
        res = self.sess.get(url=self.full_url(path), auth=('x', self.api_key) if self.api_key else None)
        res.raise_for_status()
        return res.json()

    def prepare(self, path, method, body):
        pass

    def full_url(self, path):
        return '{}/{}'.format(
            self.url,
            path
        )


class RPCClient(BaseClient):
    def __init__(self, url, api_key):
        super().__init__(url, api_key)

    def exec_rpc(self, method, *args):
        res = self.post_json('', {
            'method': method,
            'params': args
        })
        if 'error' in res and res['error'] is not None:
            err = res['error']
            raise RPCError(err['message'], err['code'])
        return res['result']

    def get_info(self):
        return self.exec_rpc('getinfo')

    def get_raw_mempool(self, verbose=True):
        return self.exec_rpc('getrawmempool', verbose)

    def get_network_hash_ps(self, blocks=120, height=1):
        return self.exec_rpc('getnetworkhashps', blocks, height)


class NodeClient(BaseClient):
    def __init__(self, url, api_key):
        super().__init__(url, api_key)

    def get_tx_by_hash(self, tx_hash):
        return self.get_json('tx/{}'.format(tx_hash))

    def get_block(self, hash_or_height):
        return self.get_json('block/{}'.format(hash_or_height))

    def get_server_info(self):
        return self.get_json('')


class NodeRPCClient(RPCClient):
    def __init__(self, url, api_key):
        super().__init__(url, api_key)

    def get_block_by_height(self, height, include_tx=True, verbose=True):
        return self.exec_rpc('getblockbyheight', height, include_tx, verbose)

    def get_info(self):
        return self.exec_rpc('getinfo')


class ClientHolder:
    def __init__(self, factory):
        self.factory = factory
        self.value = None

    def init_app(self, app):
        self.value = self.factory(app)

    def __getattr__(self, item):
        return getattr(self.value, item)


node_client = ClientHolder(lambda app: NodeClient(
    url=app.config['HSD_HOST'],
    api_key=app.config['HSD_API_KEY']
))

node_rpc_client = ClientHolder(lambda app: NodeRPCClient(
    url=app.config['HSD_HOST'],
    api_key=app.config['HSD_API_KEY']
))
