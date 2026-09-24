from enum import Enum
import glob
from io import BytesIO
import os
import wave

import sflc


def read_int(o, s: int = 4, signed: bool = False) -> int:
    return int.from_bytes(o.read(s), byteorder='little', signed=signed)


class TYPE(Enum):
    sflc = 0x02
    bfdc = 0x00


def decrypt_and_dump_file(path: str) -> None:
    base_name = os.path.basename(path).rsplit('.', 1)[0]
    with open(path, 'rb') as o:

        assert o.read(8) == b'Spitfire'
        file_mode = read_int(o)
        assert file_mode <= 1
        num_chunks = read_int(o)
        assert num_chunks <= 0x400000

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
            iden = data_chunk['00']
            base_path = 'samples/%07d %s' % (iden, base_name)
            data_type = TYPE(data_chunk['06'])

            o.seek(data_chunk['10'])
            raw_data = o.read(data_chunk['08'])

            if data_type == TYPE.sflc:
                sflc_path = '%s.sflc' % base_path
                wav_path = '%s.wav' % base_path

                if os.path.exists(wav_path):
                    continue

                sflc_data = sflc.decrypt_sflc(raw_data, iden)
                open(sflc_path, 'wb').write(sflc_data)
                sflc.process_sflc_stream(
                    wave.open(wav_path, 'wb'),
                    BytesIO(initial_bytes=sflc_data),
                )
                print('%50s' % base_path)

            else:
                save_path = '%s.%s' % (base_path, data_type.name)
                open(save_path, 'wb').write(raw_data)


if __name__ == '__main__':
    dump = {
        **{
            os.path.basename(p): decrypt_and_dump_file(p)
            for p in glob.glob(r'C:\Users\USER\Splice\INSTRUMENT\*\Samples\*.spitfire')
        },
    }
