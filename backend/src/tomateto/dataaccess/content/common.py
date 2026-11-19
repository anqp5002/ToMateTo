"""Domain snapshots and normalization; no provider I/O or implicit commit."""

from dataclasses import asdict
from typing import Any, TypeVar, cast

from tomateto.domain.content.records import (
    DishRecord,
    MediaAssetRecord,
    MediaCleanupJobRecord,
    PostImageRecord,
    PostRecord,
    RestaurantRecord,
)

Record = (
    DishRecord
    | MediaAssetRecord
    | MediaCleanupJobRecord
    | PostImageRecord
    | PostRecord
    | RestaurantRecord
)
T = TypeVar("T", bound=Record)


def snapshot(cls: type[T], row: Any) -> T:
    return cast(T, cls(**dict(row)))


def values(record: Record, *, include_id: bool = True) -> dict[str, Any]:
    result = asdict(record)
    if not include_id or result.get("id") == 0:
        result.pop("id", None)
    return result
