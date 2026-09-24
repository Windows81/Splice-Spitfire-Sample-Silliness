from itertools import cycle, islice
from io import BufferedIOBase
import itertools
import struct
import hashlib
import wave


def derive_sflc_key(iden: int) -> bytes:
    iden_payload = int.to_bytes(iden, byteorder='little', length=4)
    return hashlib.md5(hashlib.md5(iden_payload).hexdigest().encode() + b'Sp!tFiR3').digest()


def xor(data: bytes, key: bytes, offset: int = 0) -> bytes:
    return bytes(a ^ b for a, b in zip(data, islice(cycle(key), offset % len(key), None)))


def xor_calibrate(data: bytes, key: bytes, offset: int = 0):
    return xor(xor(data, key), key, offset)


def split_into_ints(data: bytes, offset: int, bytes_to_read: int, int_size: int) -> list[int]:
    base_data = bytearray(data[offset: offset + bytes_to_read])
    if bytes_to_read % int_size > 0:
        fill_pattern = 0xBAADF00D.to_bytes(4, byteorder='little')
        trail = (fill_pattern * (int_size // 4))[bytes_to_read % int_size:]
        base_data.extend(trail)

    return [
        int.from_bytes(
            bytes=base_data[(i+0)*int_size:(i+1)*int_size],
            byteorder='little',
            signed=True,
        )
        for i in range(len(base_data) // int_size)
    ]


def bitscan_not(x: int) -> int:
    x &= (1 << 64) - 1
    return (~((x + 1) ^ x)).bit_length() - 2


# sub_141B66100
def _sub_141B66100(a1: list[int], a2: int, a3: tuple[int, int, int, int]) -> None:
    if a2 <= 4:
        return
    v3 = a3[0]
    v5 = a3[1]
    v7 = a3[2]
    v8 = a3[3]
    v4 = 2
    v6 = a2 - 4
    v9 = a1[0]
    v10 = a1[2]
    while v6 > 0:
        v11 = a1[v4 - 1]
        v12 = a1[v4 + 1]
        v4 += 1
        v14 = (v5 * v10) + (v7 * v11) + (v3 * v12) + (v8 * v9)
        v10 = v12
        v9 = v11
        a1[v4+1] += v14 >> 8
        v6 -= 1


# sub_141B66060
def _sub_141B66060(a1: list[int], a2: int, a3: tuple[int, int, int, int]) -> None:
    if a2 <= 4:
        return
    v3 = a1[2]
    v4 = 2
    v6 = a2 - 4
    v5 = a3[0]
    v7 = a3[1]
    v8 = a3[2]
    while v6 > 0:
        v9 = a1[v4 + 1]
        v10 = a1[v4 - 1]
        v4 += 1
        v11 = v7 * v3
        v3 = v9
        v14 = v11 + (v5 * v9) + (v8 * v10)
        a1[v4 + 1] += v14 >> 8
        v6 -= 1


# sub_141B66200
def _sub_141B66200(a1: list[int], a2: int, a3: tuple[int, int, int, int]) -> None:
    if a2 <= 4:
        return
    v2 = 4
    v3 = a2 - 4
    while v3 > 0:
        a1[v2] = a1[v2] + 2 * a1[v2 - 1] - a1[v2 - 2]
        v2 += 1
        v3 -= 1


# sub_141B66000
def _sub_141B66000(a1: list[int], a2: int, a3: tuple[int, int, int, int]) -> None:
    if a2 <= 4:
        return
    v3 = a3[0]
    v4 = a3[1]
    v5 = 4
    v6 = a2 - 4
    while v6 > 0:
        v7 = a1[v5 - 2]
        v8 = a1[v5 - 1]
        v14 = (v3 * v8) + (v4 * v7)
        a1[v5] += v14 >> 8
        v5 += 1
        v6 -= 1


# sub_141B661D0
def _sub_141B661D0(a1: list[int], a2: int, a3: tuple[int, int, int, int]) -> None:
    if a2 <= 4:
        return
    v3 = 4
    v4 = a2 - 4
    while v4 > 0:
        v14 = a1[v3] + a1[v3 - 1]
        a1[v3] = v14
        v3 += 1
        v4 -= 1


# sub_141B65FB0
def _sub_141B65FB0(a1: list[int], a2: int, a3: tuple[int, int, int, int]) -> None:
    if a2 <= 4:
        return
    v3 = a3[0]
    v4 = 4
    v5 = a2 - 4
    while v5 > 0:
        v14 = (v3 * a1[v4 - 1]) >> 8
        a1[v4] = v14
        v4 += 1
        v5 -= 1


def _process_data(ablk_values: list[int], data_chunk: bytes) -> list[int]:
    v5 = ablk_values[2]
    (head, v10, _, v35, v36, v40, v41) = split_into_ints(data_chunk, 0, 0x1C, 4)
    v6 = min(4, v5)
    result = split_into_ints(
        data=data_chunk, offset=0x1C,
        bytes_to_read=4*v6, int_size=4,
    )
    result += [0] * (v5-v6)
    if v5 <= 4:
        return result

    v11 = v10 - 0x24
    a2 = split_into_ints(
        data=data_chunk, offset=0x1C + 4 * v6,
        bytes_to_read=v11, int_size=8,
    )

    v13 = 0
    v14 = 0
    v15 = 0
    v16 = v5 - 4
    v21 = data_chunk[0x0B]
    v22 = 4
    if v21 != 0:
        while v16 != 0:
            # Skips to next value is v15 is exhausted.
            if v15 == 0:
                v14 = a2[v13]
                v13 += 1
                v15 = 64
            v23 = 0
            while True:
                # Skips value if all bits are 1.
                while v14 == -1:
                    v14 = a2[v13]
                    v13 += 1
                    v23 += v15
                    v15 = 64
                v24 = bitscan_not(v14)
                v23 += v24
                if v24 < v15:
                    break
                v14 = a2[v13]
                v13 += 1
                v15 = 64
            v14 >>= (v24 + 1)
            v15 -= (v24 + 1)
            if v15 == 0:
                v14 = a2[v13]
                v13 += 1
                v15 = 64
            v27 = v14
            v28 = v15
            if v15 < v21:
                v30 = a2[v13]
                v13 += 1
                v31 = v14 & ((1 << v15) - 1)
                v32 = 1 << (v21 - v15)
                v14 = v30 >> (v21 - v15)
                v15 = 64 - (v21 - v15)
                v32 = v31 | ((v30 & (v32 - 1)) << v28)
            else:
                v15 -= v21
                v14 >>= v21
                v32 = v27 & ((1 << v21) - 1)
            v23 = v32 | (v23 << v21)
            v34 = -(v23 >> 1)
            if v23 & 1 == 0:
                v34 = v23 >> 1
            result[v22] = v34
            v22 += 1
            v16 -= 1
    else:
        while v16 != 0:
            if v15 == 0:
                v14 = a2[v13]
                v13 += 1
                v15 = 64
            v23 = 0
            while True:
                while v14 == -1:
                    v14 = a2[v13]
                    v13 += 1
                    v23 += v15
                    v15 = 64
                v24 = bitscan_not(v14)
                v23 += v24
                if v24 < v15:
                    break
                v14 = a2[v13]
                v13 += 1
                v15 = 64
            v14 >>= (v24 + 1)
            v15 -= (v24 + 1)
            v34 = -(v23 >> 1)
            if (v23 & 1) == 0:
                v34 = v23 >> 1
            result[v22] = v34
            v22 += 1
            v16 -= 1

    if v41 != 0:
        _sub_141B66100(result, v5, (v35, v36, v40, v41))
    elif v40 != 0:
        _sub_141B66060(result, v5, (v35, v36, v40, v41))
    elif v36 != 0:
        if v35 == 0x200 and v36 == -0x100:
            _sub_141B66200(result, v5, (v35, v36, v40, v41))
        else:
            _sub_141B66000(result, v5, (v35, v36, v40, v41))
    else:
        if v35 == 0x100:
            _sub_141B661D0(result, v5, (v35, v36, v40, v41))
        else:
            _sub_141B65FB0(result, v5, (v35, v36, v40, v41))

    return result


def _read_int(o, s: int = 4, signed: bool = False) -> int:
    return int.from_bytes(o.read(s), byteorder='little', signed=signed)


def process_sflc_stream(w: wave.Wave_write, data: BufferedIOBase) -> bytes:
    assert data.read(0x04) == b'SFLC'
    _read_int(data, 2)  # ¿? probably always 0x00
    _read_int(data, 2)  # ¿? probably always 0x01
    _read_int(data, 2)  # ¿? probably always 0x18

    num_channels = _read_int(data, 2)
    sample_rate = _read_int(data, 4)
    data_size = _read_int(data, 4)

    w.setnchannels(num_channels)
    w.setsampwidth(4)
    w.setframerate(sample_rate)

    _read_int(data, 4)  # ¿? probably always 0x0400

    accum_channel_data = [list[float]() for _ in range(num_channels)]
    next_ablk_index = data.tell()
    while (head := data.read(0x04)) == b'ABLK':

        ablk_values = [
            int.from_bytes(head, byteorder='little'),
            _read_int(data, 4),
            _read_int(data, 4),
        ]
        ablk_size = ablk_values[1]
        next_ablk_index += ablk_size
        next_ablk_index += 8

        for channel_index in range(num_channels):
            assert (head := data.read(0x04)) == b'DATA'
            data_chunk = head + data.read(0x1C)
            data_size = int.from_bytes(
                data_chunk[0x04:0x08],
                byteorder='little',
            )
            data_chunk += data.read(data_size - 0x18)
            processed_ints = _process_data(ablk_values, data_chunk)
            processed_ints = [
                v * (1 << 8)
                for v in processed_ints
            ]
            accum_channel_data[channel_index].extend(processed_ints)

    combined = list(itertools.chain(*zip(*accum_channel_data)))
    packed_data = struct.pack(
        "<{}i".format(len(combined)),
        *combined,
    )
    w.setnframes(len(accum_channel_data[0]))
    w.writeframes(packed_data)
    return packed_data


if __name__ == '__main__':
    # p = r'C:\Users\USER\Projects\splice\samples\INSTRUMENT_Common_IR_04B43E'
    p = r'C:\Users\USER\Projects\splice\samples\LABSOPIA_01_14FC45'
    with (
        wave.open(p + '.wav', 'wb') as w,
        open(file=p + '.sflc', mode='rb') as s
    ):
        result_data = process_sflc_stream(w, s)


def decrypt_sflc(raw_data: bytes, iden: int) -> bytes:
    sflc_key = derive_sflc_key(iden)
    return xor(raw_data, sflc_key)
