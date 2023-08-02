#!/usr/bin/env python3

from PIL import Image
import math
import itertools
import sys


def encode(in_file: str, out_file: str) -> None:
    with open(in_file, 'rb') as fd:
        raw = fd.read()

    r_len = len(raw)

    footer = bytearray(int.to_bytes(math.ceil(r_len / 3), 9, 'big'))
    filler_bytes = (3 - r_len % 3)
    footer[0] = filler_bytes

    # filler bytes for last data pixel + 72-bit pixel count footer
    extra_bytes = len(footer) + filler_bytes
    w = math.ceil(math.sqrt((r_len + extra_bytes)/3))
    h = w

    out = Image.new('RGB', (w, h))
    out_data = out.load()

    for i, (y, x) in zip(
        range(0, r_len, 3),
        itertools.product(range(h), range(w))
    ):
        t = tuple(raw[i:i+3])
        if len(t) < 3:
            t = t + (0,) * (3 - len(t))
        out_data[x, y] = t

    for i in range(3):
        out_data[w-4+i, h-1] = tuple(footer[i*3:(i+1)*3])

    out.save(out_file)


def decode(in_file: str, out_file: str) -> None:
    with open(in_file, 'rb') as img_fd, open(out_file, 'wb+') as fd:
        img = Image.open(img_fd)
        w, h = img.size
        img_data = img.load()

        footer = bytes(num for i in range(3) for num in img_data[w-4+i, h-1])
        out_size = int.from_bytes(footer[1:], 'big')
        filler_num = footer[0]

        for i, (y, x) in zip(
            range(out_size),
            itertools.product(range(h), range(w))
        ):
            fd.write(bytes(img_data[x, y]))

        fd.seek(-filler_num, 2)
        fd.truncate()


def main() -> None:
    assert len(sys.argv) == 4
    en_de, in_file, out_file = sys.argv[1:4]
    if en_de == 'encode':
        encode(in_file, out_file)
    elif en_de == 'decode':
        decode(in_file, out_file)
    else:
        print(f'{sys.argv[0]} <encode | decode> <input file> <output file>')


if __name__ == '__main__':
    main()
