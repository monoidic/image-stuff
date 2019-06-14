#!/usr/bin/env python3

import binascii

def parse_png(raw):
  if raw[:8] != b'\x89PNG\r\n\x1a\n':
    return # not a PNG
  ret = []
  parseraw = raw[8:]
  while parseraw:
    chunklen = int.from_bytes(parseraw[:4], 'big')
    chunktype = parseraw[4:8]
    chunkdata = parseraw[8:8+chunklen]
#    chunkcrc = parseraw[chunklen+8:chunklen+12]
    ret.append((chunktype, chunkdata))
    parseraw = parseraw[chunklen+12:]
    if chunktype == b'IEND' and parseraw:
      print('Additional data after end of image')
      ret.append(('Additional', parseraw))
  return ret

if __name__ == '__main__':
  import sys
  if len(sys.argv) < 2:
    print('Enter path to PNG file (and optionally a second one to test reverse parsing)')
    exit(1)
  fname = sys.argv[1]
  with open(fname, 'rb') as fd:
    pngraw = fd.read()
  parsed = parse_png(pngraw)
  out = [(name, len(data)) for name, data in parsed]
  print(out)
#  print(parsed)
