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


def convert_pixel(pixel, type):
    if type == 0 or type == 1:
        # RGB8888
        return struct.unpack('4B', pixel)
    elif type == 2:
        # RGB4444
        pixel, = struct.unpack('<H', pixel)
        return (((pixel >> 12) & 0xF) << 4, ((pixel >> 8) & 0xF) << 4,
                ((pixel >> 4) & 0xF) << 4, ((pixel >> 0) & 0xF) << 4)
    elif type == 3:
        # RBGA5551
        pixel, = struct.unpack('<H', pixel)
        return (((pixel >> 11) & 0x1F) << 3, ((pixel >> 6) & 0x1F) << 3,
                ((pixel >> 1) & 0x1F) << 3, ((pixel) & 0xFF) << 7)
    elif type == 4:
        # RGB565
        pixel, = struct.unpack("<H", pixel)
        return (((pixel >> 11) & 0x1F) << 3, ((pixel >> 5) & 0x3F) << 2, (pixel & 0x1F) << 3)
    elif type == 6:
        # LA88 = Luminance Alpha 88
        pixel, = struct.unpack("<H", pixel)
        return (pixel >> 8), (pixel >> 8), (pixel >> 8), (pixel & 0xFF)
    elif type == 10:
        # L8 = Luminance8
        pixel, = struct.unpack("<B", pixel)
        return pixel, pixel, pixel
    else:
        raise Exception("Unknown pixel type {}.".format(type))


def process_sc(baseName, data, path, decompress):
    if decompress:
        version = None

        if data[:2] == b'SC':
            # Skip the header if there's any
            version = int.from_bytes(data[2: 6], 'big')
            hash_length = int.from_bytes(data[6: 10], 'big')
            data = data[10 + hash_length:]

        if version in (None, 1, 3):  # Version 2 in HDP does not use any compression
            if data[:4] == b'SCLZ':
                print('[*] Detected LZHAM compression !')

                dict_size = int.from_bytes(data[4:5], 'big')
                uncompressed_size = int.from_bytes(data[5:9], 'little')

                try:
                    decompressed = lzham.decompress(data[9:], uncompressed_size, {'dict_size_log2': dict_size})

                except Exception as exception:
                    print('Cannot decompress {} !'.format(baseName))
                    return

            elif data[:4] == bytes.fromhex('28 B5 2F FD'):
                print('[*] Detected Zstandard compression !')

                try:
                    decompressed = zstandard.decompress(data)

                except Exception as exception:
                    print('Cannot decompress {} !'.format(baseName))
                    return

            else:
                print('[*] Detected LZMA compression !')
                data = data[0:9] + (b'\x00' * 4) + data[9:]

                try:
                    decompressed = lzma.LZMADecompressor().decompress(data)

                except Exception as exception:
                    print('Cannot decompress {} !'.format(baseName))
                    return

            print('[*] Successfully decompressed {} !'.format(baseName))

        else:
            decompressed = data

    else:
        decompressed = data

    writer = BinaryWriter()

    writer.write(decompressed)
    
    with open('de'+format(baseName)+'.sc', 'wb') as f:
            f.write(writer.buffer)

    print('[*] deCompression done !')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract png files from Supercell "*_tex.sc" files')
    parser.add_argument('files', help='sc file', nargs='+')
    parser.add_argument('-o', help='Extract pngs to directory', type=str)
    parser.add_argument('-d', '--decompress', help='Try to decompress _tex.sc before processing it', action='store_true')

    args = parser.parse_args()

    if args.o:
        path = os.path.normpath(args.o) + '/'

    else:
        path = os.path.dirname(os.path.realpath(__file__)) + '/'

    for file in args.files:
        basename, _ = os.path.splitext(os.path.basename(file))

        with open(file, 'rb') as f:
            print('[*] Processing {}'.format(f.name))
            process_sc(basename, f.read(), path, args.decompress)

