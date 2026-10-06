import unittest

from base32_geohash_encoder import (
    ALPHABET,
    ENCODE_MAP,
    decode,
    decode_bits,
    encode,
    encode_bits,
)


class TestAlphabet(unittest.TestCase):
    def test_alphabet_length(self):
        self.assertEqual(len(ALPHABET), 32)

    def test_alphabet_no_omitted_chars(self):
        for ch in "ailo":
            self.assertNotIn(ch, ALPHABET)

    def test_encode_map_inverse(self):
        for i, ch in enumerate(ALPHABET):
            self.assertEqual(ENCODE_MAP[ch], i)


class TestEncode(unittest.TestCase):
    def test_zero_pads_to_length(self):
        self.assertEqual(encode(0, 4), "0000")

    def test_single_char_values(self):
        for i in range(32):
            self.assertEqual(encode(i, 1), ALPHABET[i])

    def test_known_multichar(self):
        # 0b 11000 01011 -> 0b11000=24='s', 0b01011=11='c'
        # value = 24*32 + 11 = 779
        self.assertEqual(encode(779, 2), "sc")

    def test_max_capacity(self):
        # 6 chars -> 30 bits -> max = 2**30 - 1
        self.assertEqual(encode((1 << 30) - 1, 6), "zzzzzz")

    def test_over_capacity_raises(self):
        with self.assertRaises(ValueError):
            encode(1 << 30, 6)

    def test_negative_value_raises(self):
        with self.assertRaises(ValueError):
            encode(-1, 2)

    def test_negative_length_raises(self):
        with self.assertRaises(ValueError):
            encode(0, -1)

    def test_zero_length(self):
        self.assertEqual(encode(0, 0), "")


class TestDecode(unittest.TestCase):
    def test_known_string(self):
        self.assertEqual(decode("sc"), (779, 10))

    def test_roundtrip_single_char(self):
        for i in range(32):
            ch = ALPHABET[i]
            self.assertEqual(decode(ch), (i, 5))

    def test_all_chars_roundtrip(self):
        for length in (1, 2, 5):
            for value in (0, 1, 17, (1 << (5 * length)) - 1):
                s = encode(value, length)
                self.assertEqual(decode(s), (value, 5 * length))

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            decode("")

    def test_invalid_char_raises(self):
        with self.assertRaises(ValueError):
            decode("a")

    def test_uppercase_rejected(self):
        with self.assertRaises(ValueError):
            decode("S")


class TestEncodeBits(unittest.TestCase):
    def test_basic(self):
        # 0b11000 01011 = 'sc'
        self.assertEqual(encode_bits("1100001011", 2), "sc")

    def test_pads_with_zeros(self):
        # 4 bits given, length 1 -> padded to 5 bits
        self.assertEqual(encode_bits("1010", 1), ALPHABET[0b10100])

    def test_empty_to_zero_length(self):
        self.assertEqual(encode_bits("", 0), "")

    def test_invalid_bit_char(self):
        with self.assertRaises(ValueError):
            encode_bits("102", 1)

    def test_too_many_bits(self):
        with self.assertRaises(ValueError):
            encode_bits("1" * 6, 1)

    def test_negative_length(self):
        with self.assertRaises(ValueError):
            encode_bits("", -1)


class TestDecodeBits(unittest.TestCase):
    def test_known(self):
        self.assertEqual(decode_bits("sc"), "1100001011")

    def test_preserves_leading_zeros(self):
        self.assertEqual(decode_bits("0"), "00000")

    def test_roundtrip(self):
        for bits in ("", "0", "1", "10100", "1010001011", "0000000000"):
            length = (len(bits) + 4) // 5
            if length == 0:
                continue
            s = encode_bits(bits, length)
            decoded = decode_bits(s)
            # decode_bits returns exactly 5*len(s) bits, which may be
            # longer than the input due to zero-padding.
            self.assertEqual(decoded[: len(bits)] if bits else "", bits)
            self.assertEqual(len(decoded), 5 * length)

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            decode_bits("")


if __name__ == "__main__":
    unittest.main()
