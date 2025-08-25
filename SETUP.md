# Project Setup

## Install uv
### 1. Install rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
### 2. Install uv


#### Standalone (Windows)
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
#### Scoop (Windows)
```bash
scoop install main/uv
```

#### Homebrew (Mac)
```bash
brew install uv
```

### 3. Install python
```bash
uv python install 3.13
```
---
## Vscode Setup
Select `.venv` as the python interpreter (included `.ipynb` files)

### Formatter (black or ruff)
- Vscode [Ruff Formatter](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) (recommended)
- Vscode [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter) and [isort](https://marketplace.visualstudio.com/items?itemName=ms-python.isort)

---

## Adding/removing dependencies (`pip install` like)
```
uv add <package>
uv remove <package>
```

---

## Run python files
```bash
uv run <filename>.py
uv run python <filename>.py
```