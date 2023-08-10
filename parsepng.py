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

    @staticmethod
    def from_fd(fd: BytesIO, validate_crc: bool = False) -> 'ChunkData':
        first = fd.read(4)
        if len(first) != 4:
            raise ValueError('unexpected early end of file')
        chunklen = int.from_bytes(first, 'big')
        chunktype = fd.read(4)
        chunkdata = fd.read(chunklen)
        crc = fd.read(4)
        if len(crc) != 4:
            raise ValueError('unexpected early end of file')

        if validate_crc:
            correct_crc = zlib.crc32(chunktype + chunkdata)
            if crc != struct.pack(be_int, correct_crc):
                raise ValueError('invalid crc')

        return ChunkData(chunktype, chunkdata)

    def to_fd(self, fd: BytesIO) -> None:
        fd.write(struct.pack(be_int, len(self.chunkdata)))
        fd.write(self.chunktype)
        fd.write(self.chunkdata)
        crc = zlib.crc32(self.chunktype + self.chunkdata)
        fd.write(struct.pack(be_int, crc))


def get_png_chunks(fd: BytesIO) -> Iterable[ChunkData]:
    if fd.read(8) != png_header:
        raise ValueError('not a PNG')

    while True:
        chunk = ChunkData.from_fd(fd, True)
        yield chunk
        if chunk.chunktype == b'IEND':
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

        chunk.to_fd(fd)


def dedup(it: Iterable[str]) -> Iterable[str]:
    prev = None
    count = 1

    for s in it:
        if prev is None:
            prev = s
            continue

        if prev == s:
            count += 1
            continue

        yield prev if count == 1 else f'{prev} x {count}'

        count = 1
        prev = s

    if prev is not None:
        yield prev if count == 1 else f'{prev} x {count}'


def main() -> None:
    if len(sys.argv) < 2:
        print(
            'Enter path to PNG file (and optionally a second one '
            'to test reverse parsing)'
        )
        return

    fname = sys.argv[1]
    with open(fname, 'rb') as fd:
        for s in dedup(f'{chunk.chunktype.decode()} ({len(chunk.chunkdata)} bytes)' for chunk in get_png_chunks(fd)):
            print(s)

        if len(sys.argv) != 3:
            return
        fd.seek(0)
        out_name = sys.argv[2]
        with open(out_name, 'wb') as out_fd:
            chunks_to_file(out_fd, get_png_chunks(fd))


if __name__ == '__main__':
    main()
