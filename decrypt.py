import blowfish
import functools
import glob
import hashlib
import json
import os

JUCE_B64_ENCODE = b".ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+"
JUCE_B64_DECODE = {v: i for (i, v) in enumerate(JUCE_B64_ENCODE)}


def juce_base64_decode(encoded_str: bytes):
    dot_idx = encoded_str.find(b'.')
    num_bytes = int(encoded_str[:dot_idx])
    data_part = encoded_str[dot_idx + 1:]

    result = bytearray(num_bytes)

    bit_pos = 0
    for ch in data_part:
        bits_to_set = JUCE_B64_DECODE[ch]
        byte_idx = bit_pos >> 3
        offset_in_byte = bit_pos & 7
        bits_remaining = 6

        while bits_remaining > 0 and byte_idx < num_bytes:
            bits_this_time = min(bits_remaining, 8 - offset_in_byte)
            mask = ((1 << bits_this_time) - 1)
            result[byte_idx] |= (bits_to_set & mask) << offset_in_byte

            byte_idx += 1
            bits_to_set >>= bits_this_time
            bits_remaining -= bits_this_time
            offset_in_byte = 0

        bit_pos += 6

    return bytes(result)


def _get_bit_range(size: int, data: bytes, bitRangeStart: int, num_bits: int) -> int:
    res = 0
    byte = bitRangeStart >> 3
    offset = bitRangeStart & 7
    bits_done = 0
    while num_bits > 0 and byte < size:
        bits_this_time = min(num_bits, 8 - offset)
        mask = (0xff >> (8 - bits_this_time)) << offset
        res |= (((data[byte] & mask) >> offset) << bits_done)
        bits_done += bits_this_time
        num_bits -= bits_this_time
        byte += 1
        offset = 0
    return res


# code from https://github.com/asb2m10/dexed/discussions/402
def juce_base64_encode(data: bytes) -> bytes:
    size = len(data)
    l = ((len(data) << 3) + 5) // 6
    s = bytearray(b'%d.' % size)
    for i in range(l):
        res = 0
        bitRangeStart = i*6
        byte = bitRangeStart // 8
        offsetInByte = bitRangeStart % 8
        bitsSoFar = 0
        numBits = 6

        while numBits > 0 and byte < size:
            bitsThisTime = min(numBits, 8 - offsetInByte)
            mask = (0xff >> (8 - bitsThisTime)) << offsetInByte

            res |= (((data[byte] & mask) >> offsetInByte) << bitsSoFar)

            bitsSoFar += bitsThisTime
            numBits -= bitsThisTime
            byte += 1
            offsetInByte = 0

        s.append(JUCE_B64_ENCODE[res])
    return bytes(s)


@functools.cache
def derive_config_key() -> bytes:
    plaintext = b'ANCQ49-DCJB4E-JMLW53-LMMR54-MKNM52-PGRD55-SGTW4D-TCM045-4E5400'
    xml_key = b''.join([
        hashlib.sha256(juce_base64_encode(plaintext + b'storeCH')).digest(),
        hashlib.sha256(juce_base64_encode(plaintext + b'storePT')).digest(),
    ])

    xml_payload = (
        b'<?xml version="1.0" encoding="UTF-8"?> <key store="%s" Pr="%d" P0="%d"/>' %
        (xml_key.hex(sep='-', bytes_per_sep=4).upper().encode(), 3, 0)
    )

    return b''.join([
        hashlib.sha256(juce_base64_encode(xml_payload + b'keyCH')).digest(),
        hashlib.sha256(juce_base64_encode(xml_payload + b'keyPT')).digest(),
    ])


CONFIG_KEY = derive_config_key()
assert CONFIG_KEY == bytes.fromhex(
    'B14A925B C23EEFF3 3417E725 38DE153F B6EA6C91 59B251EC CDF6F562 EC6FC791 2D3814A4 31882627 8FFAFD87 D75D4482 DC57E8D3 F130A467 B7142BEC DF4EE8D5'
)

PRESET_KEY = bytes.fromhex(
    'D460B854 9CF7C78A 55D2447B 9CCB0FDE 5BA64F67 5BD6361E 7D852863 7E3F511E 73F239F0 C1F7BE9A B64BA87E 0DB21C63 69422A5E 5DCACE7F 4B783E41 C622CBA2',
)


@functools.cache
def get_decryptor(key: bytes):
    return blowfish.Cipher(key=CONFIG_KEY, byte_order='little').decrypt_ecb


@functools.cache
def decrypt_chunks(key: bytes, chunk: bytes):
    result = b''.join(get_decryptor(key)(chunk))
    trim_len = result[-1]
    assert 0 <= trim_len <= 8
    return result[:-trim_len]


def decrypt_zfile(p: str, key: bytes) -> bytes:
    result = []
    with open(p, 'rb') as o:
        size = int.from_bytes(o.read(4), byteorder='little')
        chunk_batch = (size & 0xFFFFFFFFFFFFFFF8) + 8

        while (d := o.read(chunk_batch)):
            r = decrypt_chunks(key, d)
            result.append(r)

    return b''.join(result)


def main():
    dump = {
        **{
            os.path.basename(p): json.loads(decrypt_zfile(p, CONFIG_KEY))
            for p in glob.glob(r'c:\Users\USER\Splice\INSTRUMENT\*\Patches\*\*')
        },
        **{
            os.path.basename(p): json.loads(decrypt_zfile(p, PRESET_KEY))
            for p in glob.glob(r'c:\Users\USER\Splice\INSTRUMENT\*\Presets\*\*')
        },
    }
    json.dump(dump, open('saved_presets.json', 'w'), indent='\t')


if __name__ == '__main__':
    main()
