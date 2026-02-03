# Reliability

Built-in reliability features for production deployments.

## Overview

PraisonAI-SVC includes comprehensive reliability features to handle failures gracefully.

## Exponential Backoff

Worker polling uses exponential backoff:

```
Initial wait: 1 second
Max wait: 30 seconds

1s → 2s → 4s → 8s → 16s → 30s → 30s...
```

This reduces load on Azure Queue Storage during idle periods.

## Retry Logic

Job processing includes automatic retry:

| Attempt | Wait | Action |
|---------|------|--------|
| 1st | - | Process job |
| 2nd | 5s | Retry after failure |
| 3rd | 10s | Final retry |
| - | - | Move to poison queue |

## Poison Queue

Failed jobs after max retries are moved to a poison queue:

- Queue name: `{queue-name}-poison`
- Jobs remain for manual inspection
- Can be replayed after fixing issues

## Timeout Detection

Jobs have a configurable timeout:

```bash
# Default: 10 minutes
PRAISONAI_MAX_JOB_DURATION_MINUTES=10
```

Jobs exceeding timeout are marked as failed.

## Idempotency

Prevent duplicate job processing:

- **JobHash**: SHA256 of payload
- Duplicate requests return existing job ID
- No duplicate work performed

## Error Handling

Comprehensive error messages for debugging:

```json
{
  "job_id": "abc123",
  "status": "failed",
  "error": "Connection timeout to external API",
  "retry_count": 3,
  "created_at": "2025-11-04T21:00:15Z",
  "failed_at": "2025-11-04T21:05:20Z"
}
```

## Health Checks

Endpoint for container orchestration:

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "service": "my-service",
  "version": "1.0.0"
}
```

## Autoscaling Support

Compatible with Azure Container Apps scaling:

```yaml
scale:
  minReplicas: 0      # Scale to zero when idle
  maxReplicas: 3      # Cap for cost control
  rules:
    - name: http
      type: http
      metadata:
        concurrentRequests: "50"
```
