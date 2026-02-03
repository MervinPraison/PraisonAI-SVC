# PraisonAI SVC

Turn PraisonAI packages into Azure web services.

```mermaid
graph LR
    A[🐍 Python Package] --> B[🔌 PraisonAI SVC]
    B --> C[☁️ Azure Service]
    
    style A fill:#6366F1,stroke:#7C90A0,color:#fff
    style B fill:#10B981,stroke:#7C90A0,color:#fff
    style C fill:#0EA5E9,stroke:#7C90A0,color:#fff
```

## Quick Start

```bash
pip install praisonai-svc
praisonai-svc deploy
```

## Features

| Feature | Description |
|---------|-------------|
| ☁️ Azure | Azure Functions deployment |
| 🚀 FastAPI | Built on FastAPI |
| 📦 Docker | Container support |

## Next Steps

- [Installation](getting-started/installation.md)
- [Deployment](getting-started/deployment.md)
