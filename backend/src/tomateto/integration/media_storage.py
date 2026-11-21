"""Durable local NFR-10 storage. Never expose the storage directory as static files."""

import warnings
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from tomateto.business.content.contracts import invalid
from tomateto.shared.exceptions import DomainError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@dataclass(frozen=True)
class ProcessedImage:
    content: bytes
    width: int
    height: int


def process_image(content: bytes) -> ProcessedImage:
    if len(content) > MAX_UPLOAD_BYTES:
        raise DomainError("PAYLOAD_TOO_LARGE")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise invalid("file", "UNSUPPORTED_TYPE")
                source.load()
                image = ImageOps.exif_transpose(source).convert("RGB")
                image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                result = BytesIO()
                image.save(result, format="JPEG", quality=85)
                return ProcessedImage(result.getvalue(), image.width, image.height)
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise invalid("file", "UNSUPPORTED_TYPE") from None


class LocalMediaStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def path(self, key: str) -> Path:
        target = (self.root / key).resolve()
        if not key or not target.is_relative_to(self.root) or target == self.root:
            raise ValueError("Invalid storage key")
        return target

    def store(self, key: str, content: bytes) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.path(key).open("xb") as target:
            target.write(content)

    def remove(self, key: str) -> None:
        self.path(key).unlink(missing_ok=True)
