#!/usr/bin/env python3

import sys
import struct
import functools
import json

prefix_len = 11
suffix_len = 16

_convert = lambda fmt, size: lambda fd: struct.unpack(fmt, fd.read(size))[0]
byte     = _convert('=B', 1)
le_uint2 = _convert('<H', 2)
le_uint4 = _convert('<I', 4)
#be_uint4 = _convert('>I', 4)

def error(s):
    print(s)
    sys.exit(1)

def parse_prefix(fd, json_encodable):
    ret = {
        'magic': fd.read(5),
        'version': byte(fd),
        'size': le_uint4(fd),
        'targets': byte(fd)
    }

    if ret['magic'] != b'DfuSe' or ret['version'] != 1:
        error('Invalid/unexpected constants in prefix')

    if json_encodable:
        ret['magic'] = ret['magic'].decode()

    return ret


def parse_suffix(fd, json_encodable):
    ret = {
        'bcd_device': le_uint2(fd),
        'id_product': le_uint2(fd),
        'id_vendor': le_uint2(fd),
        'bcd_dfu': le_uint2(fd),
        'signature': fd.read(3),
        'b_length': byte(fd),
        'dfu_crc': le_uint4(fd)
    }

    if ret['bcd_dfu'] != 0x011a or ret['signature'] != b'UFD' or ret['b_length'] != 16:
        error('Invalid/unexpected constants in suffix')

    if json_encodable:
        ret['signature'] = ret['signature'].decode()

    return ret


def parse_images(fd, images_num, json_encodable):
    return [parse_image(fd, json_encodable) for _ in range(images_num)]

def parse_image(fd, json_encodable):
    data = {
        'signature': fd.read(6),
        'alternate': byte(fd),
        'named': le_uint4(fd),
        'name': fd.read(255),
        'size': le_uint4(fd),
        'n_elements': le_uint4(fd),
        'elements': None # filled in below
    }

    if data['signature'] != b'Target':
        error('Missing constant in image')

    if json_encodable:
        data['signature'] = data['signature'].decode()
        data['name'] = data['name'].hex()

    data['elements'] = [parse_image_element(fd, json_encodable) for _ in range(data['n_elements'])]

    get_len = (lambda e: len(e['data']) // 2 + 8) if json_encodable else (lambda e: len(e['data']) + 8)
    actual_size = sum(map(get_len, data['elements']))

    if data['size'] != actual_size:
        error(f'Invalid DFU image size ({actual_size=}, {data["size"]=})')

    return data

def parse_image_element(fd, json_encodable):
    ret = {
        'address': le_uint4(fd),
        'size': le_uint4(fd),
        'data': None # filled in below
    }

    ret['data'] = fd.read(ret['size'])
    if json_encodable:
        ret['data'] = ret['data'].hex()

    return ret

def parse(fd, json_encodable=True):
    prefix = parse_prefix(fd, json_encodable)

    pos = fd.seek(-suffix_len, 2) # right before suffix
    images_size = pos - prefix_len

    suffix = parse_suffix(fd, json_encodable)

    fd.seek(prefix_len, 0)
    images = parse_images(fd, prefix['targets'], json_encodable)

    return {
        'prefix': prefix,
        'images': images,
        'suffix': suffix
    }

def main():
    with open('full.dfu', 'rb') as fd:
        data = parse(fd, False)

#    with open('dump.json', 'w') as fd:
#        json.dump(data, fd)

    with open('dump.txt', 'w') as fd:
        fd.write(str(data))


if __name__ == '__main__':
    main()
