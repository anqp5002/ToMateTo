"""Lớp miền (domain) của backend.

Không tự import thực thể ở đây: test và lớp gọi import trực tiếp module cần dùng
(SPEC S8 r2 §2) để tránh phụ thuộc vòng và tải model ngoài phạm vi.
"""

__all__: list[str] = []
