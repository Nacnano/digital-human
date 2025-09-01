# Digital Human

## Setup
### Install uv
#### 1. Install rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```
#### 2. Install uv


##### Standalone (Windows)
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
##### Scoop (Windows)
```bash
scoop install main/uv
```

##### Homebrew (Mac)
```bash
brew install uv
```

#### 3. Install python
```bash
uv python install 3.13
```
