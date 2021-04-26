import binascii

from explorer.protocol import parse_name_resource

YEET_RECORDS = binascii.unhexlify(
    '0002036e73310479656574002ce706b701c00206012d66412b797154564456552b6a4e63656d4e7a612f55683677565a59394c316144744e6567526d77677032526861'
)


def test_read_label():
    print(parse_name_resource(YEET_RECORDS))
