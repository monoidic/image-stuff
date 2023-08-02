#!/usr/bin/env python3

import zlib
import struct
import sys

from io import BytesIO
from typing import Iterable
from dataclasses import dataclass

png_header = b'\x89PNG\r\n\x1a\n'
be_int = '>I'


@dataclass
class ChunkData:
    chunktype: bytes
    chunkdata: bytes


def get_png_chunks(fd: BytesIO) -> Iterable[ChunkData]:
    if fd.read(8) != png_header:
        raise ValueError('not a PNG')

    while True:
        first = fd.read(4)
        if len(first) != 4:
            raise ValueError('unexpected early end of file')
        chunklen = int.from_bytes(first, 'big')
        chunktype = fd.read(4)
        chunkdata = fd.read(chunklen)
        fd.read(4)  # crc

        yield ChunkData(chunktype, chunkdata)
        if chunktype == b'IEND':
            break

    remaining = fd.read(1)
    if remaining:
        remaining += fd.read()
        yield ChunkData(b'extra', remaining)


def chunks_to_file(fd: BytesIO, it: Iterable[ChunkData]) -> None:
    fd.write(png_header)

    for chunk in it:
        if chunk.chunktype == b'extra':
            fd.write(chunk.chunkdata)
            break

        fd.write(struct.pack(be_int, len(chunk.chunkdata)))
        fd.write(chunk.chunktype)
        fd.write(chunk.chunkdata)
        crc = zlib.crc32(chunk.chunktype + chunk.chunkdata)
        fd.write(struct.pack(be_int, crc))


def main() -> None:
    if len(sys.argv) < 2:
        print(
            'Enter path to PNG file (and optionally a second one '
            'to test reverse parsing)'
        )
        return

    fname = sys.argv[1]
    with open(fname, 'rb') as fd:
        for chunk in get_png_chunks(fd):
            print(f'{chunk.chunktype.decode()} ({len(chunk.chunkdata)} bytes)')

        if len(sys.argv) != 3:
            return
        fd.seek(0)
        out_name = sys.argv[2]
        with open(out_name, 'wb') as out_fd:
            chunks_to_file(out_fd, get_png_chunks(fd))


if __name__ == '__main__':
    main()
