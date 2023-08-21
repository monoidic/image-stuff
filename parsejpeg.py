#!/usr/bin/env python3

import os
import sys
import struct

from dataclasses import dataclass
from enum import IntEnum
from typing import Iterable, BinaryIO


be_short = '>H'


class Marker(IntEnum):
    SOI = 0xd8
    SOF0 = 0xc0
    SOF2 = 0xc2
    DHT = 0xc4
    DQT = 0xdb
    DRI = 0xdd
    SOS = 0xda

    RST0 = 0xd0
    RST1 = 0xd1
    RST2 = 0xd2
    RST3 = 0xd3
    RST4 = 0xd4
    RST5 = 0xd5
    RST6 = 0xd6
    RST7 = 0xd7

    APP0 = 0xe0
    APP1 = 0xe1
    APP2 = 0xe2
    APP3 = 0xe3
    APP4 = 0xe0
    APP5 = 0xe0
    APP6 = 0xe0
    APP7 = 0xe0
    APP8 = 0xe0
    APP9 = 0xe9
    APP10 = 0xea
    APP11 = 0xeb
    APP12 = 0xec
    APP13 = 0xed
    APP14 = 0xee
    APP15 = 0xef

    COM = 0xfe
    EOI = 0xd9

    Entropy = 0x100
    Extra = 0x101


@dataclass
class DataChunk:
    marker: Marker
    data: bytes


# number signifies static size, None signifies variable size
markerlen = {
    Marker.SOI: 0,
    Marker.SOF0: None,
    Marker.SOF2: None,
    Marker.DHT: None,
    Marker.DQT: None,
    Marker.DRI: 4,
    Marker.SOS: None,

    Marker.RST0: 0,
    Marker.RST1: 0,
    Marker.RST2: 0,
    Marker.RST3: 0,
    Marker.RST4: 0,
    Marker.RST5: 0,
    Marker.RST6: 0,
    Marker.RST7: 0,

    Marker.APP0: None,
    Marker.APP1: None,
    Marker.APP2: None,
    Marker.APP3: None,
    Marker.APP4: None,
    Marker.APP5: None,
    Marker.APP6: None,
    Marker.APP7: None,
    Marker.APP8: None,
    Marker.APP9: None,
    Marker.APP10: None,
    Marker.APP11: None,
    Marker.APP12: None,
    Marker.APP13: None,
    Marker.APP14: None,
    Marker.APP15: None,

    Marker.COM: None,
    Marker.EOI: 0,
}


def parse_to_chunks(fd: BinaryIO) -> Iterable[DataChunk]:
    # expect SOI first
    first = fd.read(2)
    if first != b'\xff\xd8':
        raise ValueError('not JPEG?')
    yield DataChunk(Marker.SOI, b'')

    while True:
        first = fd.read(1)
        if not first:
            raise ValueError('unexpected end of file')
        if first == b'\xff':
            chunk = read_chunk(fd)
        else:
            chunk = read_entropy(fd)

        yield chunk
        if chunk.marker == Marker.EOI:
            break

    remaining = fd.read()
    if remaining:
        yield DataChunk(Marker.Extra, remaining)


def read_chunk(fd: BinaryIO) -> DataChunk:
    marker = Marker(fd.read(1)[0])
    section_len = markerlen[marker]
    if section_len is None:
        section_len = struct.unpack(be_short, fd.read(2))[0] - 2
    data = fd.read(section_len)

    return DataChunk(marker, data)


def read_entropy(fd: BinaryIO) -> DataChunk:
    fd.seek(-1, os.SEEK_CUR)  # initial byte
    buf = bytearray()

    while True:
        byte = fd.read(1)
        if not byte:
            raise ValueError('unexpected early end of file')

        if byte != b'\xff':
            buf.extend(byte)
            continue

        byte = fd.read(1)
        if not byte:
            raise ValueError('unexpected early end of file')

        if byte == b'\x00':
            buf.extend(b'\xff')
            continue
        fd.seek(-2, os.SEEK_CUR)
        break

    return DataChunk(Marker.Entropy, bytes(buf))


def rev_parsed(fd: BinaryIO, it: Iterable[DataChunk]) -> None:
    for chunk in it:
        if chunk.marker == Marker.Entropy:
            fd.write(chunk.data.replace(b'\xff', b'\xff\x00'))
            continue
        elif chunk.marker == Marker.Extra:
            fd.write(chunk.data)
            break

        fd.write(b'\xff')
        fd.write(bytes([int(chunk.marker)]))
        if markerlen[chunk.marker] is None:
            fd.write(struct.pack(be_short, len(chunk.data) + 2))
        fd.write(chunk.data)


def main() -> None:
    if len(sys.argv) < 2:
        print(
            'Enter path to *single* jpeg to analyze (and a path to '
            'an output file to test reverting parsed data to a jpeg)'
        )
        return

    filename = sys.argv[1]
    with open(filename, 'rb') as fd:
        for x in parse_to_chunks(fd):
            print(x.marker.name, len(x.data))

        if len(sys.argv) != 3:
            return

        fd.seek(0)
        out_name = sys.argv[2]
        with open(out_name, 'wb') as out_fd:
            rev_parsed(out_fd, parse_to_chunks(fd))


if __name__ == '__main__':
    main()
