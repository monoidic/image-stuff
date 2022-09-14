#!/usr/bin/env python3

import zlib

png_header = b'\x89PNG\r\n\x1a\n'
def parse_png(raw):
  if raw[:8] != png_header:
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
  dat = bytearray()
  for section in ret:
    if section[0] == b'IDAT':
      dat.extend(section[1])
  ret.append(('dat', zlib.decompress(dat)))
  return ret

def revparse_png(data):
  ret = png_header
  for chunk in data:
    chunktype = chunk[0]
    chunkdata = chunk[1]
    if chunktype == 'Additional':
      ret += chunkdata
      break
    chunklen = int.to_bytes(len(chunkdata), 4, 'big')
    chunkcrc = int.to_bytes(zlib.crc32(chunktype + chunkdata), 4, 'big')
    ret += chunklen + chunktype + chunkdata + chunkcrc
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
  if len(sys.argv) != 3:
    exit(0)
  revparsed = revparse_png(parsed)
  with open(sys.argv[2], 'wb') as fd:
    fd.write(revparsed)
#  print(parsed)
