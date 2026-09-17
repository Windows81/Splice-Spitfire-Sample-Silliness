import glob
from io import BytesIO
import os
from pprint import pprint
import hashlib
from itertools import cycle, islice
import wave

import sflc


def xor(data: bytes, key: bytes, offset: int = 0) -> bytes:
    return bytes(a ^ b for a, b in zip(data, islice(cycle(key), offset % len(key), None)))


def xor_calibrate(data: bytes, key: bytes, offset: int = 0):
    return xor(xor(data, key), key, offset)


def derive_key(iden: int) -> bytes:
    iden_payload = int.to_bytes(iden, byteorder='little', length=4)
    return hashlib.md5(hashlib.md5(iden_payload).hexdigest().encode() + b'Sp!tFiR3').digest()


def read_int(o, s: int = 4, signed: bool = False) -> int:
    return int.from_bytes(o.read(s), byteorder='little', signed=signed)


def decrypt_file(path: str):
    base_name = os.path.basename(path).rsplit('.', 1)[0]
    with open(path, 'rb') as o:

        assert o.read(8) == b'Spitfire'
        file_mode = read_int(o)
        assert file_mode <= 1
        num_chunks = read_int(o)
        assert num_chunks <= 0x400000

        min_meta_1_size = 0x7FFFFFFFFFFFFFFF
        max_meta_2_size = 0x0000000000000000
        data_chunks: list[dict[str, int]] = [{} for _ in range(num_chunks)]

        for data_chunk in data_chunks:
            data_chunk.update({
                '00': read_int(o, 4),  # sample_identifier
                '04': read_int(o, 2),  # ¿? probably always 0x05
                '06': read_int(o, 2),  # ¿? probably always 0x02
                '08': read_int(o, 4),  # audio_size
                '0C': read_int(o, 4),  # metadata_size
                '10': read_int(o, 4),  # audio_seek
                '14': read_int(o, 4),  # ¿? probably always 0x00
                '18': read_int(o, 4),  # metadata_seek
                '1C': read_int(o, 4),  # ¿? probably always 0x00
            })

            # Splice INSTRUMENT does something different when that value is equal to 6.
            # Maybe it arranges the metadata fields in a different order.
            # I don't know.
            mode = data_chunk['04']
            assert mode != 6

        for data_chunk in data_chunks:
            assert data_chunk['0C'] == 0x28
            o.seek(data_chunk['18'])

            data_chunk.update({
                '20': read_int(o, 4, signed=True),  # ¿? probably always 0x01
                '24': read_int(o, 4, signed=True),  # bytes_per_sample
                '28': read_int(o, 4, signed=False),  # channel_count
                '2C': read_int(o, 4, signed=False),  # sample_rate
                '30': read_int(o, 4, signed=False),  # ¿?
                '34': read_int(o, 4, signed=True),  # ¿? probably always 0x00
                '38': read_int(o, 4, signed=True),  # ¿? probably always 0x00
                '3C': read_int(o, 4, signed=False),  # volume_float
                '40': read_int(o, 4, signed=True),  # channel_mask
                '44': read_int(o, 4, signed=False),  # ¿? probably always 0x00
            })

        for data_chunk in data_chunks:
            o.seek(data_chunk['10'])
            iden = data_chunk['00']
            key = derive_key(iden)

            raw_data = o.read(data_chunk['08'])
            base_path = 'samples/%s_%06X' % (base_name, iden)

            try:
                sflc_data = bytearray(xor(raw_data, key))
                print('%50s - %s' % (base_path, key.hex()))
                sflc.process_sflc_stream(
                    wave.open(base_path + '.wav', 'wb'),
                    BytesIO(initial_bytes=sflc_data),
                )
                open(base_path + '.sflc', 'wb').write(sflc_data)
            except AssertionError:
                pass


if __name__ == '__main__':
    dump = {
        **{
            os.path.basename(p): decrypt_file(p)
            for p in glob.glob(r'C:\Users\USER\Splice\INSTRUMENT\*\Samples\*.spitfire')
        },
    }
