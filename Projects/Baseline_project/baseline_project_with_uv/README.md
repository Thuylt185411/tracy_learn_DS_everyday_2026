# KHỞI TẠO PROJECT MỚI

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
```

Tạo `.gitignore`

```
.venv/*
__pycache__/*
.pytest_cache/*
```

Tạo các folder cần thiết

```
mkdir src
mkdir tests
mkdir notebooks
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
