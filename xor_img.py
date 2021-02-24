#!/usr/bin/env python3

import sys
from PIL import Image

def main():
    assert len(sys.argv) >= 4
    with Image.open(sys.argv[1]) as img1, Image.open(sys.argv[2]) as img2:
        assert img1.size == img2.size
        assert img1.mode == img2.mode

        with Image.new(img1.mode, img1.size) as out:
            img1_l = img1.load()
            img2_l = img2.load()
            out_l = out.load()

            w, h = img1.size
            for x in range(w):
                for y in range(h):
                    out_l[x, y] = tuple(map(lambda t: t[0] ^ t[1], zip(img1_l[x, y], img2_l[x, y])))
            out.save(sys.argv[3])

main()
