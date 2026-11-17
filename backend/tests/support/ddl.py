"""Dựng schema PostgreSQL cho test từ DDL nguyên văn của DOC 6.4-B.

S8 r2 không có `db/`/migration (SPEC §2, §5): mỗi session test tạo database
`tomateto_test` rồi dựng đúng các bảng cần cho T12–T17, T25 cùng bảng cha của
chúng. Câu lệnh được trích **nguyên văn** từ khối `BEGIN DDL` trong
`docs/thiet_ke/6.4-B_ddl.md`; không sửa, không viết lại DDL.

Hàm `apply_ddl` để TASK khác tái sử dụng.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

from sqlalchemy import Connection, Engine

REPO_ROOT: Final = Path(__file__).resolve().parents[3]
DDL_DOCUMENT: Final = REPO_ROOT / "docs" / "thiet_ke" / "6.4-B_ddl.md"

#: Bảng phục vụ T12–T17, T25 và bảng cha bắt buộc cho khóa ngoại của chúng.
REQUIRED_TABLES: Final[tuple[str, ...]] = (
    "users",
    "dishes",
    "restaurants",
    "posts",
    "likes",
    "follows",
    "collections",
    "collection_items",
    "reports",
    "notifications",
    "user_blocks",
)

#: Thứ tự xóa ngược thứ tự tạo để không vướng khóa ngoại.
DROP_ORDER: Final[tuple[str, ...]] = tuple(reversed(REQUIRED_TABLES))

_TABLE_STATEMENT = re.compile(r"^CREATE TABLE (\w+)")
_INDEX_STATEMENT = re.compile(r"^CREATE (?:UNIQUE )?INDEX \w+ ON (\w+)")
_ALTER_STATEMENT = re.compile(r"^ALTER TABLE (\w+)")
_REFERENCES = re.compile(r"REFERENCES (\w+)")
_SKIPPED_HEADS: Final[tuple[str, ...]] = (
    "BEGIN",
    "COMMIT",
    "SET LOCAL",
    "COMMENT ON",
)


def read_ddl_block(document: Path = DDL_DOCUMENT) -> str:
    """Trả khối SQL giữa `<!-- BEGIN DDL -->` và dấu ``` kết thúc."""
    text = document.read_text(encoding="utf-8")
    start = text.find("<!-- BEGIN DDL -->")
    if start < 0:
        raise RuntimeError(f"Không thấy mốc BEGIN DDL trong {document}")
    fence = text.find("```sql", start)
    if fence < 0:
        raise RuntimeError(f"Không thấy khối ```sql sau mốc BEGIN DDL trong {document}")
    body = text.find("\n", fence) + 1
    end = text.find("```", body)
    if end < 0:
        raise RuntimeError(f"Khối DDL không đóng trong {document}")
    return text[body:end]


def split_statements(sql: str) -> list[str]:
    """Tách câu lệnh theo dấu `;`, bỏ qua chuỗi, `--` comment và `$tag$`."""
    statements: list[str] = []
    buffer: list[str] = []
    index = 0
    length = len(sql)
    quote: str | None = None
    dollar_tag: str | None = None

    while index < length:
        char = sql[index]
        if dollar_tag is not None:
            if sql.startswith(dollar_tag, index):
                buffer.append(dollar_tag)
                index += len(dollar_tag)
                dollar_tag = None
                continue
            buffer.append(char)
            index += 1
            continue
        if quote is not None:
            buffer.append(char)
            if char == quote:
                quote = None
            index += 1
            continue
        if char == "-" and sql.startswith("--", index):
            newline = sql.find("\n", index)
            if newline < 0:
                break
            index = newline
            continue
        if char in {"'", '"'}:
            quote = char
            buffer.append(char)
            index += 1
            continue
        if char == "$":
            match = re.match(r"\$[A-Za-z_]*\$", sql[index:])
            if match is not None:
                dollar_tag = match.group(0)
                buffer.append(dollar_tag)
                index += len(dollar_tag)
                continue
        if char == ";":
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            index += 1
            continue
        buffer.append(char)
        index += 1

    trailing = "".join(buffer).strip()
    if trailing:
        statements.append(trailing)
    return statements


def _table_of(statement: str) -> str | None:
    for pattern in (_TABLE_STATEMENT, _INDEX_STATEMENT, _ALTER_STATEMENT):
        match = pattern.match(statement)
        if match is not None:
            return match.group(1)
    return None


def ddl_statements() -> list[str]:
    """Câu lệnh DDL đã lọc cho `REQUIRED_TABLES`, giữ nguyên thứ tự tài liệu."""
    wanted = set(REQUIRED_TABLES)
    selected: list[str] = []
    for statement in split_statements(read_ddl_block()):
        if statement.startswith(_SKIPPED_HEADS):
            continue
        if statement.startswith("CREATE EXTENSION"):
            selected.append(f"{statement};")
            continue
        table = _table_of(statement)
        if table is None or table not in wanted:
            continue
        # Câu lệnh tham chiếu bảng ngoài phạm vi (ví dụ ALTER users → media_assets).
        if set(_REFERENCES.findall(statement)) - wanted:
            continue
        selected.append(f"{statement};")
    return selected


def apply_ddl(bind: Engine | Connection) -> list[str]:
    """Xóa các bảng cũ rồi dựng lại schema test; trả danh sách câu lệnh đã chạy."""
    # Tên bảng lấy từ hằng nội bộ, không từ input người dùng.
    statements = [f"DROP TABLE IF EXISTS {table} CASCADE;" for table in DROP_ORDER]  # noqa: S608
    statements.extend(ddl_statements())
    if isinstance(bind, Engine):
        with bind.begin() as connection:
            _execute(connection, statements)
    else:
        _execute(bind, statements)
    return statements


def _execute(connection: Connection, statements: list[str]) -> None:
    for statement in statements:
        connection.exec_driver_sql(statement)
