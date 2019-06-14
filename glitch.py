#!/usr/bin/env python3

import random, parsejpeg

def full_random_section(intup):
  randdata = random.getrandbits(len(intup[1]) * 8)
  randdata = int.to_bytes(randdata, len(intup[1]), 'little')
  randdata = randdata.replace(b'\xff', b'\xfe') # no unwanted markers
  return (intup[0], randdata)

if __name__ == '__main__':
  import sys
  if len(sys.argv) < 2:
    print('Enter path to jpeg')
    exit(1)
  orig_fname = sys.argv[1]
  if orig_fname.count('/'):
    orig_fname = orig_fname[orig_fname.rfind('/')+1:]
  with open(sys.argv[1], 'rb') as fd:
    raw = fd.read()
  parsed = parsejpeg.parse_jpeg(raw)
  for i in range(len(parsed)):
    name = parsed[i][0]
    if len(parsed[i][1]) == 0 or name != 'Entropy':
      continue
    fname = f'{orig_fname}_{i}.jpg'
    glitched = parsed[:i] + [full_random_section(parsed[i])] + parsed[i+1:]
    glitched = parsejpeg.rev_parsed(glitched)
    with open(fname, 'wb') as fd:
      fd.write(glitched)
      print(f'{fname} written')
