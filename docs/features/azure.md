# Azure Integration

Native Azure services integration for reliable, cost-effective deployments.

## Overview

PraisonAI-SVC uses Azure services for storage, queuing, and job management:

- **Blob Storage** - File storage with retry logic
- **Queue Storage** - Job queue with poison queue for failures
- **Table Storage** - Job state tracking

## Architecture

```
┌─────────────────────────────────────┐
│   Azure Container App (FastAPI)     │
│  ┌──────────┐      ┌──────────┐    │
│  │   API    │      │  Worker  │    │
│  └────┬─────┘      └─────┬────┘    │
└───────┼──────────────────┼──────────┘
        │                  │
        ▼                  ▼
   ┌─────────┐        ┌─────────┐
   │  Table  │        │  Queue  │
   │ Storage │        │ Storage │
   └─────────┘        └─────────┘
                           │
                           ▼
                      ┌─────────┐
                      │  Blob   │
                      │ Storage │
                      └─────────┘
```

## Blob Storage

Store job output files with automatic retry:

- **Retry Logic**: 3 attempts with exponential backoff
- **SAS URLs**: Secure download links (1h expiry)
- **Container**: Auto-created `job-outputs`

## Queue Storage

Job queuing with reliability features:

- **Poison Queue**: Failed jobs moved after max retries
- **Visibility Timeout**: Prevents duplicate processing
- **Dead Letter**: Track permanently failed jobs

## Table Storage

Job state management:

- **Status Tracking**: pending → processing → completed/failed
- **Metadata**: Timestamps, error messages, file locations
- **Query Support**: Filter jobs by status, date, etc.

## Configuration

```bash
# .env file
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING=your_connection_string
```

**Get Connection String:**
1. Azure Portal → Storage Account
2. Security + networking → Access Keys
3. Copy connection string

## Local Testing with Azurite

Test without Azure account:

```bash
# Install Azurite
npm install -g azurite

# Start emulator
azurite --silent

# Use local connection string
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
```
