"""Core Base32 geohash codec.

This module implements only the Base32 layer of the geohash scheme: it
maps between an integer (or a string of bits) and the geohash Base32
alphabet. It deliberately knows nothing about latitude, longitude, or
cell resolution — those concerns belong to a coordinate layer that can
be built on top.

Design decisions
----------------

* The alphabet is the geohash.org variant
  ``0123456789bcdefghjkmnpqrstuvwxyz``. It omits ``a``, ``i``, ``l``,
  and ``o`` to reduce confusion with digits and with each other. This
  is the only alphabet this library handles; selecting among alphabets
  is out of scope.

* Inputs that contain characters outside the alphabet raise
  ``ValueError`` rather than being silently skipped. A partial decode
  would produce a geohash that appears valid but points somewhere
  unintended, which is worse than a loud failure.

* ``encode`` accepts any non-negative ``int`` and pads the output with
  leading ``0`` characters to the requested length. The caller is
  responsible for telling us how many characters they want, because
  the "natural" length of a bit-aligned integer is ambiguous (``0``
  could be 0 bits or 5 bits or 10 bits, all equally valid).

* ``decode`` returns ``(value, bits_consumed)``. ``bits_consumed`` is
  ``5 * len(s)`` on success, which lets callers know exactly how many
  bits of precision they received. It also lets ``encode_bits`` round-
  trip a previously decoded string even when the trailing characters
  contained leading-zero padding.
"""

from __future__ import annotations

from typing import Dict, Tuple

# The geohash.org Base32 alphabet. Order matters: the index of each
# character is the 5-bit value it represents.
ALPHABET: str = "0123456789bcdefghjkmnpqrstuvwxyz"

# Precomputed reverse lookup. Building it once at import time keeps the
# hot path in ``decode`` to a simple dict hit with no per-call overhead.
ENCODE_MAP: Dict[str, int] = {ch: i for i, ch in enumerate(ALPHABET)}


def encode(value: int, length: int) -> str:
    """Encode a non-negative integer into ``length`` Base32 characters.

    The integer is interpreted as a big-endian sequence of 5-bit groups,
    least-significant group last. Output is left-padded with ``0``
    characters so that ``len(result) == length``.

    Why ``length`` is required: a bit-aligned integer has no canonical
    width. ``0`` is representable in 0, 5, 10, ... bits, and each choice
    yields a different geohash string. Forcing the caller to state the
    width removes that ambiguity.

    Args:
        value: Non-negative integer to encode.
        length: Desired output length in characters. Must be >= 0.

    Returns:
        The encoded string, of exactly ``length`` characters.

    Raises:
        ValueError: If ``value`` is negative, or ``length`` is
            negative, or ``value`` does not fit in ``5 * length`` bits.
    """
    if length < 0:
        raise ValueError(f"length must be non-negative, got {length}")
    if value < 0:
        raise ValueError(f"value must be non-negative, got {value}")

    capacity = (1 << (5 * length)) - 1
    if value > capacity:
        raise ValueError(
            f"value {value} does not fit in {length} characters "
            f"(max {capacity})"
        )

    chars = []
    remaining = value
    # Walk from the least-significant 5-bit group to the most-
    # significant, then reverse so the string reads MSB-first.
    for _ in range(length):
        chars.append(ALPHABET[remaining & 0x1F])
        remaining >>= 5
    return "".join(reversed(chars))


def decode(s: str) -> Tuple[int, int]:
    """Decode a Base32 geohash string to an integer.

    Args:
        s: String over the geohash alphabet. Case-sensitive: the
            alphabet is lower-case, so upper-case letters are rejected.

    Returns:
        A pair ``(value, bits_consumed)`` where ``value`` is the decoded
        integer and ``bits_consumed`` is ``5 * len(s)``.

    Raises:
        ValueError: If ``s`` is empty or contains a character not in
            the alphabet.
    """
    if not s:
        raise ValueError("cannot decode empty string")

    value = 0
    for ch in s:
        try:
            digit = ENCODE_MAP[ch]
        except KeyError:
            raise ValueError(
                f"character {ch!r} is not in the geohash Base32 alphabet"
            ) from None
        value = (value << 5) | digit
    return value, 5 * len(s)


def encode_bits(bits: str, length: int) -> str:
    """Encode a binary string into ``length`` Base32 characters.

    ``bits`` is read left-to-right as a big-endian bit stream. It is
    right-padded with zero bits to reach a multiple of 5, then each
    5-bit group is mapped to one character.

    Args:
        bits: String of ``0`` and ``1`` characters. May be empty.
        length: Desired number of output characters. The padded bit
            stream must not exceed ``5 * length`` bits.

    Returns:
        The encoded string of exactly ``length`` characters.

    Raises:
        ValueError: If ``bits`` contains characters other than ``0``
            and ``1``, or if the padded stream is longer than
            ``5 * length`` bits, or if ``length`` is negative.
    """
    if length < 0:
        raise ValueError(f"length must be non-negative, got {length}")

    if any(c not in "01" for c in bits):
        bad = next(c for c in bits if c not in "01")
        raise ValueError(
            f"bits must contain only '0' and '1', found {bad!r}"
        )

    total_bits = 5 * length
    if len(bits) > total_bits:
        raise ValueError(
            f"{len(bits)} bits do not fit in {length} characters "
            f"(max {total_bits} bits)"
        )

    padded = bits.ljust(total_bits, "0")
    out = []
    for i in range(0, total_bits, 5):
        group = int(padded[i : i + 5], 2)
        out.append(ALPHABET[group])
    return "".join(out)


def decode_bits(s: str) -> str:
    """Decode a Base32 geohash string to a raw bit string.

    Each character contributes exactly 5 bits, most-significant first.
    The result is the concatenation of those 5-bit groups with no
    trimming: trailing zero bits introduced by the encoder's padding
    are preserved. Callers that know how many meaningful bits they
    encoded should truncate the result themselves.

    Args:
        s: String over the geohash alphabet.

    Returns:
        A string of ``5 * len(s)`` characters, each ``0`` or ``1``.

    Raises:
        ValueError: If ``s`` is empty or contains a character outside
            the alphabet.
    """
    value, n_bits = decode(s)
    # Format with leading zeros so every 5-bit group is preserved,
    # including leading-zero characters in the input.
    return format(value, "0{}b".format(n_bits))
