#!/usr/bin/env python3

table = {
  b'\xff\xd8': 'SOI',  b'\xff\xc0': 'SOF0',
  b'\xff\xc2': 'SOF2', b'\xff\xc4': 'DHT',
  b'\xff\xdb': 'DQT',  b'\xff\xdd': 'DRI',
  b'\xff\xda': 'SOS',  b'\xff\xfe': 'COM',
  b'\xff\xd9': 'EOI'
} # RSTn, APPn

revtable = { val: key for key, val in table.items() }

markerlen = { # number signifies static size, None signifies variable size
  'SOI': 0, 'SOF0': None, 'SOF2': None, 'DHT': None,
  'DQT': None, 'DRI': 4, 'SOS': None, 'COM': None,
  'EOI': 0
} # RSTn, APPn

def get_section_type(header):
  if header in table:
    name = table[header]
    return (name, markerlen[name])
  elif b'\xff\xd0' <= header <= b'\xff\xd7':
    n = header[1] ^ 0x70
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
  elif name == 'Entropy':
    pass
  else:
    return
  ret += data # body
  return ret

def parse_jpeg(raw):
  ret = []
  if raw[:2] != b'\xff\xd8': # if not a jpeg
    return
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
    if name == 'EOI':
      return ret
    parseraw = parseraw[size:]
  return ret

def rev_parsed(parsed):
  out = b''
  for section in parsed:
    out += get_section_bytes(section)
  return out

if __name__ == '__main__':
  import sys

  if len(sys.argv) < 2:
    print('Enter path to jpeg')
    exit(1)

  with open(sys.argv[1], 'rb') as fd:
    injpeg = fd.read()
  parsed_jpeg = parse_jpeg(injpeg)
#  print(parsed_jpeg)
  print([x for x, _y in parsed_jpeg])

  if len(sys.argv) < 3:
    exit(0)

  revparsed = rev_parsed(parsed_jpeg)
  with open(sys.argv[2], 'wb') as fd:
    fd.write(revparsed)
