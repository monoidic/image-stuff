#!/usr/bin/env python3

import sys
import itertools
from PIL import Image


def main():
    assert len(sys.argv) >= 4
    in1, in2, outp = sys.argv[1:4]
    with Image.open(in1) as img1, Image.open(in2) as img2:
        if img1.size != img2.size:
            raise ValueError('image sizes do not match')
        if img1.mode != img2.mode:
            raise ValueError('image modes do not match')

        with Image.new(img1.mode, img1.size) as out:
            img1_l = img1.load()
            img2_l = img2.load()
            out_l = out.load()

            w, h = img1.size
            for x, y in itertools.product(range(w), range(h)):
                out_l[x, y] = tuple(
                    pix1 ^ pix2
                    for pix1, pix2 in zip(img1_l[x, y], img2_l[x, y]))
            out.save(outp)


if __name__ == '__main__':
    main()
