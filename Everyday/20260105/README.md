Ngày 5/1/2025

# 1. Cách quản lý bằng uv

Nay mình viết lại về cách quản lý thư viện Python phổ biến và pipeline cơ bản

Ngày trước thưởng lưu bằng `requirement.txt` - phải cấu hình cơ bản, thủ công nên tốc độ chậm, thiếu thư viện, không tốt

## Xu hướng hiện nay đang sử dụng `uv`

```
# KHỞI TẠO PROJECT MỚI
uv init baseline_project_with_uv
cd baseline_project_with_uv

#THÊM DEPENDENCIES - dev need ... venv - docs need sphinx
uv add requests pandas numpy
uv add --group dev pytest ruff black mypy 
uv add --group docs sphinx

#TẠO LOCK FILE (tự động, nhưng có thể chạy)
uv lock

#CÀI ĐẶT TOÀN BỘ
uv sync

#CHẠY CODE
uv run python main.py
uv run pytest

#CẬP NHẬT DEPENDENCIES
uv add requests@2.32.0  # Version cụ thể
uv sync                  # Cập nhật environment
```

## Cấu Trúc File Project UV

```plaintext
my_project/
├── pyproject.toml
├── uv.lock
├── README.md
├── .gitignore
├── .venv/               # Virtual env (tự động)
├── src/
│   └── my_package/
│       └── __init__.py
└── tests/
    └── test_*.py
```

## Migrating từ requirements.txt → uv

```bash
# 1. Khởi tạo uv project
uv init .

# 2. Import từ requirements.txt cũ
uv add -r requirements.txt

# 3. Xóa requirements.txt cũ (tuỳ chọn)
rm requirements.txt

# 4. Commit uv.lock vào git
git add pyproject.toml uv.lock
```

## uv (Tốt Nhất - 2025+)

```bash
uv init
uv add requests django
uv sync
uv run python main.py
```

## Makefile / CI-CD Pipeline Điển Hình

```makefile
.PHONY: install dev test lint format run

# Setup project
install:
	uv sync

# Install with dev dependencies
dev:
	uv sync --all-groups

# Chạy tests
test:
	uv run pytest -n auto --cov

# Lint & format
lint:
	uv run ruff check .
	uv run mypy src/

format:
	uv run black src/ tests/
	uv run ruff check --fix .

# Chạy ứng dụng
run:
	uv run python src/main.py

# Docker/Deployment
build:
	uv lock
	uv export -o requirements.txt

```

COMMIT:

```makefile
pyproject.toml (luôn)

uv.lock (để reproducibility)

.gitignore include .venv/
```

Dependency Groups:

```bash
uv add django              # Production
uv add --group dev pytest  # Development only
uv add --group test pytest-cov  # Testing

```

Python Version Management:

```bash
uv python pin 3.12      # Lock vào Python 3.12
uv run python --version # Tự động dùng pinned version

```

# 2. Cách sử dụng evidently và các chỉ số đánh giá

Định hướng:

- Sử dụng evidently để sử dụng các metrics phổ biến, stress_test với evidently xem tốc độ xử lý với số feature nhất định, số dòng records nhất định
- Tạo bảng kết quả tính các chỉ số để có thể sử dụng để thực hiện vẽ báo cáo


COMMENTS

- Chưa thực hiện bước này vội => PLAN trước đã - chưa hoàn thành plan, tối sẽ tìm hiểu và mai hoàn thành plan trước khi làm
