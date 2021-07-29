import os
import sys
import lzma
import lzham
import struct
import argparse
import zstandard
import hashlib

from PIL import Image
from Writer import BinaryWriter

def process_lzma(baseName, data, path, compress):
    if compress:
        print('[*] Compressing texture with lzma')

        filters = [
                    {
                    "id": lzma.FILTER_LZMA1,
                    "dict_size": 256 * 1024,
                    "lc": 3,
                    "lp": 0,
                    "pb": 2,
                    "mode": lzma.MODE_NORMAL
                    },
                    ]

        compressed = lzma.compress(data, format=lzma.FORMAT_ALONE, filters=filters)
        compressed = compressed[0:5] + len(data).to_bytes(4, 'little') + compressed[13:]
    else:
        compressed = data

    writer = BinaryWriter()

    writer.write(compressed)
    
    with open('Comp'+format(baseName)+'.sc', 'wb') as f:
            f.write(writer.buffer)

    print('[*] Compression done !')

def process_lzham(baseName, data, path, compress):
    if compress:
        print('[*] Compressing texture with lzham')

        dict_size = 18

        compressed = lzham.compress(data, {'dict_size_log2': dict_size})
        compressed = 'SCLZ'.encode('utf-8') + dict_size.to_bytes(1, 'big') + len(data).to_bytes(4, 'little') + compressed
    else:
        compressed = data

    writer = BinaryWriter()

    writer.write(compressed)
    
    with open('Comp'+format(baseName)+'.sc', 'wb') as f:
            f.write(writer.buffer)

    print('[*] Compression done !')        
        
def process_zstd(baseName, data, path, compress):
    if compress:
        print('[*] Compressing texture with zstandard')
        compressed = zstandard.compress(data, level=zstandard.MAX_COMPRESSION_LEVEL)
    else:
        compressed = data

    writer = BinaryWriter()

    writer.write(compressed)
    
    with open('Comp'+format(baseName)+'.sc', 'wb') as f:
            f.write(writer.buffer)

    print('[*] Compression done !')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract png files from Supercell "*_tex.sc" files')
    parser.add_argument('files', help='sc file', nargs='+')
    parser.add_argument('-o', help='Extract pngs to directory', type=str)
    parser.add_argument('-c', '--compress', help='Try to compress _tex.sc before processing it', action='store_true')
    parser.add_argument('-lzma', '--lzma', help='enable LZMA compression', action='store_true')
    parser.add_argument('-lzham', '--lzham', help='enable LZHAM compression', action='store_true')
    parser.add_argument('-zstd', '--zstd', help='enable Zstandard compression', action='store_true')

    args = parser.parse_args()

    if args.o:
        path = os.path.normpath(args.o) + '/'

    else:
        path = os.path.dirname(os.path.realpath(__file__)) + '/'

    for file in args.files:
        basename, _ = os.path.splitext(os.path.basename(file))
        
    if (args.lzham, args.lzma, args.zstd).count(True) == 1:
        if args.lzham:
            with open(file, 'rb') as f:
                print('[*] Processing {}'.format(f.name))
                process_lzham(basename, f.read(), path, args.compress)
            
        if args.lzma:
            with open(file, 'rb') as f:
                print('[*] Processing {}'.format(f.name))
                process_lzma(basename, f.read(), path, args.compress)
                
        if args.zstd:
            with open(file, 'rb') as f:
                print('[*] Processing {}'.format(f.name))
                process_zstd(basename, f.read(), path, args.compress)
