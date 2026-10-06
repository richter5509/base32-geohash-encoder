"""Base32 Geohash Encoder.

A focused implementation of the Base32 variant used by the geohash.org
encoding scheme. The alphabet and bit-packing convention follow the
original geohash specification (Gustavo Niemeyer, 2008): each character
encodes 5 bits, characters are concatenated MSB-first, and bits are
consumed in order to interleave longitude and latitude.
"""

from .core import (
    ALPHABET,
    ENCODE_MAP,
    decode,
    decode_bits,
    encode,
    encode_bits,
)

__all__ = [
    "ALPHABET",
    "ENCODE_MAP",
    "decode",
    "decode_bits",
    "encode",
    "encode_bits",
]
