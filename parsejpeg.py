#!/usr/bin/env python3

import io

from typing import Optional

table = {
    b'\xff\xd8': 'SOI',  b'\xff\xc0': 'SOF0',
    b'\xff\xc2': 'SOF2', b'\xff\xc4': 'DHT',
    b'\xff\xdb': 'DQT',  b'\xff\xdd': 'DRI',
    b'\xff\xda': 'SOS',  b'\xff\xfe': 'COM',
    b'\xff\xd9': 'EOI',
} # RSTn, APPn

revtable = { val: key for key, val in table.items() }

markerlen = { # number signifies static size, None signifies variable size
    'SOI': 0, 'SOF0': None, 'SOF2': None, 'DHT': None,
    'DQT': None, 'DRI': 4, 'SOS': None, 'COM': None,
    'EOI': 0,
} # RSTn, APPn

def get_section_type(header: bytes) -> Optional[tuple[str, int]]:
    if header in table:
        name = table[header]
        return (name, markerlen[name])
    elif b'\xff\xd0' <= header <= b'\xff\xd7':
        n = header[1] ^ 0xd0
        return (f'RST{n}', 0) # 0
    elif b'\xff\xe0' <= header <= b'\xff\xef':
        n = header[1] ^ 0xe0
        return (f'APP{n}', None) # None

def get_section_bytes(intup):
  """ return full section (header, size, body) from header+body """
  ret = b''
  name = intup[0]
  data = intup[1]
  if name in markerlen:
    ret += revtable[name] # header
    if markerlen[name] == None:
      ret += int.to_bytes(len(data)+2, 2, 'big') # length
  elif name[:3] == 'RST':
    num = int(name[3:])
    ret += bytes([0xff, 0xd0 + num]) # header
  elif name[:3] == 'APP':
    num = int(name[3:])
    ret += bytes([0xff, 0xe0 + num]) # header
    ret += int.to_bytes(len(data)+2, 2, 'big') #length
  elif name == 'Entropy' or name == 'OTHERDATA':
    pass
  else:
    return
  ret += data # body
  return ret

def parse_jpeg(raw):
  if raw[:2] != b'\xff\xd8': # if not a jpeg
      return
  ret = []
  parseraw = raw
  while parseraw:
      curr_header = parseraw[:2]
      type = get_section_type(curr_header)
      if type == None: # entropy-encoded data
          offset = 0
          while True:
              parse_offset = parseraw[offset:] # offset to work from, in case of 0xff00
              if not parse_offset: # if end of file is hit
                  return ret
              ent_size = parse_offset.find(b'\xff') + offset
              if parseraw[ent_size:ent_size+2] == b'\xff\x00': # skip past 0xff00
                  offset = ent_size + 1
                  continue
              ret.append(('Entropy', parseraw[:ent_size])) # add entropy section
              parseraw = parseraw[ent_size:]
              break
          continue
      name, size = type
      if size == None:
          size = int.from_bytes(parseraw[2:4], 'big') - 2 #ignore size section
          parseraw = parseraw[4:] # skip past marker and size
      else:
          parseraw = parseraw[2:] # skip past marker
      ret.append((name, parseraw[:size]))
      parseraw = parseraw[size:]
      if name == 'EOI' and parseraw:
          print('Additional data after end of image')
          ret.append(('OTHERDATA', parseraw[size:]))
          return ret
  return ret

def parse_jpeg2(fd: io.BytesIO) -> list[tuple[str, bytes]]:
    fd.seek(0)
    if fd.read(3) != b'\xff\xd8\xff':
        raise Exception('invalid jpeg')
    fd.seek(0)
    ret = []
    while True:
        section_hdr = fd.read(2)
        if not section_hdr:
            break
        section_t = get_section_type(section_hdr)
        if not section_t:
            ret.append(('Entropy', read_entropy(fd)))
            continue
        section_name, section_len = section_t
        if section_len is None:
            section_len = int.from_bytes(fd.read(2), 'big') - 2
        ret.append((section_name, fd.read(section_len)))

        if section_name == 'EOI':
            rest = fd.read()
            if rest:
                ret.append(('OTHERDATA', rest))
            break
        

    return ret

def read_entropy(fd: io.BytesIO) -> bytes:
    buf = bytearray()
    while True:
        b = fd.read(1)[0]
        if b != 0xff:
            buf.append(b)
            continue
        
        # ff00 or next header
        if fd.read(1)[0] == 0:
            buf.extend(b'\xff\x00')
        else:
            fd.seek(-2, 1)
            break
    
    return bytes(buf)


def rev_parsed(parsed):
    return b''.join(get_section_bytes(section) for section in parsed)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print('Enter path to *single* jpeg to analyze (and a path to an output file to test reverting parsed data to a jpeg)')
        exit(1)
    with open(sys.argv[1], 'rb') as fd:
        parsed_jpeg = parse_jpeg2(fd)

    for name, data in parsed_jpeg:
        print(name, len(data))
#  print([(x, f'{len(y)} bytes') for x, y in parsed_jpeg])

    if len(sys.argv) != 3:
        exit(0)

    revparsed = rev_parsed(parsed_jpeg)
    with open(sys.argv[2], 'wb') as fd:
        fd.write(revparsed)
