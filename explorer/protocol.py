import binascii
import hashlib
import io
import re

import bech32


class NetworkMain:
    def __init__(self):
        self.__dict__ = {
            'auction_start': 2016,
            'rollout_interval': 1008,
            'lockup_period': 4320,
            'renewal_window': 105120,
            'renewal_period': 26208,
            'renewal_maturity': 4320,
            'claim_period': 210240,
            'claim_frequency': 288,
            'bidding_period': 720,
            'reveal_period': 1440,
            'tree_interval': 36,
            'transfer_lockup': 288,
            'revocation_delay': 2016,
            'auction_maturity': 4176,
            'blocks_per_day': 144
        }


network_main = NetworkMain()


def valid_name(name):
    return re.match(r'^((?!-)[a-z0-9-]{1,63}(?<!-))+$', name) is not None


def hash_name(name):
    h = hashlib.sha3_256(name.encode('ascii'))
    return h.hexdigest()


def parse_address(version, h):
    return bech32.encode('hs', int(version), binascii.unhexlify(h))


def validate_address(addr):
    try:
        _, data = bech32.decode('hs', addr)
        return data is not None
    except Exception as e:
        return False


def read_byte(rd):
    out = rd.read(1)
    return out[0] if len(out) > 0 else None


def read_length_prefixed(rd):
    return rd.read(read_byte(rd))


def read_label(buf, off, follow_pointer=True):
    labels = []
    while True:
        label_len = int(buf[off])
        if label_len == 0x00:
            return labels, off + 1

        if label_len >= 0xc0:
            if not follow_pointer:
                return labels, off + 1
            off += 1
            pointee = int.from_bytes(bytearray([label_len - 0xc0, buf[off]]), 'big')
            pointed_labels, _ = read_label(buf, pointee, follow_pointer=False)
            labels += pointed_labels
            return labels, off + 1

        start = off + 1
        end = start + label_len
        label = buf[start:end]
        labels.append(str(label.decode('ascii')))
        off = end


class DSRecord:
    def __init__(self, key_tag, algorithm, digest_type, digest):
        self.key_tag = key_tag
        self.algorithm = algorithm
        self.digest_type = digest_type
        self.digest = digest

    @classmethod
    def read(cls, rd):
        return cls(
            key_tag=int.from_bytes(rd.read(2), 'big'),
            algorithm=int(read_byte(rd)),
            digest_type=int(read_byte(rd)),
            digest=read_length_prefixed(rd)
        )


class NSRecord:
    def __init__(self, ns):
        self.ns = ns

    @classmethod
    def read(cls, rd, raw):
        ns, off = read_label(raw, rd.tell())
        rd.seek(off)
        return cls(
            ns='.'.join(ns)
        )


class GlueRecord:
    def __init__(self, address_type, ns, address):
        self.address_type = address_type
        self.ns = ns
        self.address = address

    @classmethod
    def read4(cls, rd, raw):
        ns, off = read_label(raw, rd.tell())
        rd.seek(off)
        address = rd.read(4)
        return cls(
            address_type='IPv4',
            ns='.'.join(ns),
            address='.'.join([str(octet) for octet in address])
        )

    @classmethod
    def read6(cls, rd, raw):
        ns, off = read_label(raw, rd.tell())
        rd.seek(off)
        address = rd.read(4)
        return cls(
            address_type='IPv6',
            ns='.'.join(ns),
            address=':'.join([str(octet) for octet in address])
        )


class SynthRecord:
    def __init__(self, address_type, address):
        self.address_type = address_type
        self.address = address

    @classmethod
    def read4(cls, rd):
        address = rd.read(4)
        return cls(
            address_type='IPv4',
            address='.'.join([str(octet) for octet in address])
        )

    @classmethod
    def read6(cls, rd):
        address = rd.read(16)
        return cls(
            address_type='IPv6',
            address=':'.join([str(octet) for octet in address])
        )


class TXTRecord:
    def __init__(self, entries):
        self.entries = entries

    @classmethod
    def read(cls, rd):
        entry_count = int(read_byte(rd))
        entries = []
        for i in range(0, entry_count):
            entries.append(read_length_prefixed(rd))
        return cls(
            entries=entries
        )


def parse_name_resource(resource_buf):
    out = {
        'DS': [],
        'NS': [],
        'GLUE4': [],
        'GLUE6': [],
        'SYNTH4': [],
        'SYNTH6': [],
        'TXT': []
    }

    if resource_buf is None or len(resource_buf) == 0:
        return out

    rd = io.BytesIO(resource_buf)
    ver = int(read_byte(rd))
    if ver != 0x00:
        raise Exception('Invalid serialization version.')

    while True:
        rectype = read_byte(rd)
        if rectype is None:
            return out
        rectype = int(rectype)

        if rectype == 0x00:
            out['DS'].append(DSRecord.read(rd))
        elif rectype == 0x01:
            out['NS'].append(NSRecord.read(rd, resource_buf))
        elif rectype == 0x02:
            out['GLUE4'].append(GlueRecord.read4(rd, resource_buf))
        elif rectype == 0x03:
            out['GLUE6'].append(GlueRecord.read6(rd, resource_buf))
        elif rectype == 0x04:
            out['SYNTH4'].append(SynthRecord.read4(rd))
        elif rectype == 0x05:
            out['SYNTH6'].append(SynthRecord.read6(rd))
        elif rectype == 0x06:
            out['TXT'].append(TXTRecord.read(rd))
