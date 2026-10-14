# Base32 Geohash Encoder

Encodes and decodes the Base32 alphabet variant used by the geohash.org geographic coordinate hashing scheme.

```python
from base32_geohash_encoder import encode, decode, encode_bits, decode_bits, ALPHABET

# Integer <-> string
s = encode(651, 2)          # -> "sc"
value, nbits = decode(s)    # -> (651, 10)

# Bit string <-> string
s2 = encode_bits("1010001011", 2)  # -> "sc"
bits = decode_bits(s2)             # -> "1010001011"
```

## Why this exists

Geohashing interleaves longitude and latitude bits into a single stream, then packs that stream 5 bits at a time into a Base32 string using a specific alphabet (`0123456789bcdefghjkmnpqrstuvwxyz`). This library implements only that Base32 layer: the mapping between integers, bit strings, and characters. It does not handle coordinate ranges, cell resolution, or neighbor lookups — those are separable concerns that belong to a coordinate layer built on top.

The trade-off is deliberately narrow scope. A single, well-tested alphabet and a strict round-trip contract are more valuable here than configurability that would invite ambiguity.

## Edge cases

- `encode(0, length)` returns a string of `0` characters. The `length` argument is required because a bit-aligned integer has no canonical width.
- `decode` rejects upper-case letters and the characters `a`, `i`, `l`, `o` (which are absent from the alphabet). Invalid input raises `ValueError` rather than producing a silently truncated result.
- `decode_bits` preserves trailing zero bits introduced by padding. If you encode 4 bits into 1 character, decoding yields 5 bits; truncate the result yourself if you know the original length.

## Exports

- `ALPHABET` — the 32-character geohash Base32 alphabet.
- `ENCODE_MAP` — dict mapping each alphabet character to its 5-bit value.
- `encode(value: int, length: int) -> str`
- `decode(s: str) -> tuple[int, int]` — returns `(value, bits_consumed)`.
- `encode_bits(bits: str, length: int) -> str`
- `decode_bits(s: str) -> str`

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

