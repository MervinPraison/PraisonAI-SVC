# PraisonAI SVC - Agent Instructions

## Project Structure
```
PraisonAI-SVC/
├── pyproject.toml        # Version: 1.2.0
├── src/praisonai_svc/
├── docker/
├── deploy.sh
└── docs/
```

## Version: `pyproject.toml` line 3

## CLI: `praisonai-svc`

## Commands
```bash
praisonai-svc run      # Local dev
praisonai-svc deploy   # Deploy to Azure
```

## Development
```bash
uv pip install -e ".[dev]"
pytest
```
