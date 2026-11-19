"""Valid PNG fixtures constructed locally; no downloaded images or provider calls."""

import struct
import zlib
from pathlib import Path


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack("!I", len(payload))
        + kind
        + payload
        + struct.pack("!I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def png(width: int, height: int, *, target_bytes: int | None = None) -> bytes:
    header = b"\x89PNG\r\n\x1a\n" + chunk(
        b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    )
    pixels = (b"\0" + b"\x80\x80\x80" * width) * height
    body = header + chunk(b"IDAT", zlib.compress(pixels))
    ending = chunk(b"IEND", b"")
    if target_bytes is not None:
        padding = target_bytes - len(body) - len(ending) - 12
        if padding < 0:
            raise ValueError("Target size is smaller than PNG content")
        # Ancillary/private/safe-to-copy chunk; keeps the PNG structurally valid.
        body += chunk(b"fiXt", bytes(padding))
    return body + ending


def write_nfr05_fixtures(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "valid_9_9mb.png").write_bytes(png(1, 1, target_bytes=int(9.9 * 1024**2)))
    (directory / "too_large_10_1mb.png").write_bytes(png(1, 1, target_bytes=int(10.1 * 1024**2)))
    (directory / "not_image.txt").write_text("Not an image fixture", encoding="utf-8")
    (directory / "wide_2000.png").write_bytes(png(2000, 1))
