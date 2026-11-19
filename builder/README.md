# PWServer Package Build Helper

## How to Use

[Install uv](https://docs.astral.sh/uv/getting-started/installation/) and run the commands from `builder/`.

Run the helper:
```bash
uv run build
```

Run the code checks:
```bash
uv run ruff check .
uv run ruff format --check .
```

Update all dependencies:
```bash
uv sync --upgrade
```
