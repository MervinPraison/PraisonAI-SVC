# Deployment

## Azure Functions

```bash
praisonai-svc deploy --azure
```

## Docker

```bash
docker build -t praisonai-svc .
docker run -p 8000:8000 praisonai-svc
```

## Local Development

```bash
praisonai-svc run
```
