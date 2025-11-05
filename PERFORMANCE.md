# Performance Testing Guide

This guide shows how to test the performance of your deployed PraisonAI service.

---

## Quick Performance Test

### 1. Single Request Speed Test

```bash
# Test health endpoint response time
time curl https://YOUR-APP.azurecontainerapps.io/health

# Example output:
# {"status":"healthy","service":"my-service"}
# real    0m0.234s  ← Response time
```

### 2. Job Processing Speed Test

```bash
# Create a job and measure total time
START=$(date +%s)

# Create job
JOB_ID=$(curl -s -X POST https://YOUR-APP.azurecontainerapps.io/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "Speed Test"}}' | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Wait for completion
while true; do
  STATUS=$(curl -s https://YOUR-APP.azurecontainerapps.io/jobs/$JOB_ID | jq -r '.status')
  echo "Status: $STATUS"
  
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  
  sleep 1
done

END=$(date +%s)
DURATION=$((END - START))
echo "Total time: ${DURATION}s"
```

---

## Load Testing with Apache Bench (ab)

### Install Apache Bench

```bash
# macOS (comes with macOS)
which ab

# Ubuntu/Debian
sudo apt-get install apache2-utils

# Check version
ab -V
```

### Test 1: Health Endpoint Load Test

```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 https://YOUR-APP.azurecontainerapps.io/health

# 1000 requests, 50 concurrent
ab -n 1000 -c 50 https://YOUR-APP.azurecontainerapps.io/health
```

**Key Metrics:**
- **Requests per second** - How many requests/sec
- **Time per request** - Average response time
- **Failed requests** - Should be 0

### Test 2: Job Creation Load Test

```bash
# Create a test payload file
cat > job-payload.json << 'EOF'
{"payload": {"title": "Load Test Job"}}
EOF

# 50 job creation requests, 5 concurrent
ab -n 50 -c 5 -p job-payload.json -T application/json \
  https://YOUR-APP.azurecontainerapps.io/jobs
```

---

## Load Testing with wrk (Advanced)

### Install wrk

```bash
# macOS
brew install wrk

# Ubuntu/Debian
sudo apt-get install wrk
```

### Test 1: Simple Load Test

```bash
# 10 threads, 100 connections, 30 seconds
wrk -t10 -c100 -d30s https://YOUR-APP.azurecontainerapps.io/health
```

**Output Example:**
```
Running 30s test @ https://YOUR-APP.azurecontainerapps.io/health
  10 threads and 100 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency   234.56ms   45.23ms   1.23s    89.45%
    Req/Sec    42.34     12.45    78.00     67.89%
  12678 requests in 30.01s, 2.34MB read
Requests/sec:    422.45
Transfer/sec:     79.87KB
```

### Test 2: Job Creation with Custom Script

Create `wrk-job-test.lua`:

```lua
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
wrk.body = '{"payload": {"title": "Load Test"}}'
```

Run test:

```bash
wrk -t10 -c50 -d30s -s wrk-job-test.lua \
  https://YOUR-APP.azurecontainerapps.io/jobs
```

---

## Load Testing with k6 (Recommended)

### Install k6

```bash
# macOS
brew install k6

# Ubuntu/Debian
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

### Test Script: `performance-test.js`

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 50 },   // Ramp up to 50 users
    { duration: '30s', target: 100 }, // Ramp up to 100 users
    { duration: '1m', target: 100 },  // Stay at 100 users
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests should be below 500ms
    http_req_failed: ['rate<0.01'],   // Less than 1% of requests should fail
  },
};

const BASE_URL = 'https://YOUR-APP.azurecontainerapps.io';

export default function () {
  // Test 1: Health check
  let healthRes = http.get(`${BASE_URL}/health`);
  check(healthRes, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 200ms': (r) => r.timings.duration < 200,
  });

  sleep(1);

  // Test 2: Create job
  let jobPayload = JSON.stringify({
    payload: { title: 'k6 Load Test' }
  });
  
  let jobRes = http.post(`${BASE_URL}/jobs`, jobPayload, {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(jobRes, {
    'job creation status is 200': (r) => r.status === 200,
    'job has job_id': (r) => JSON.parse(r.body).job_id !== undefined,
  });

  if (jobRes.status === 200) {
    let jobId = JSON.parse(jobRes.body).job_id;
    
    // Test 3: Check job status
    let statusRes = http.get(`${BASE_URL}/jobs/${jobId}`);
    check(statusRes, {
      'status check is 200': (r) => r.status === 200,
    });
  }

  sleep(2);
}
```

### Run k6 Test

```bash
# Update the BASE_URL in the script first
k6 run performance-test.js

# Or with custom settings
k6 run --vus 50 --duration 2m performance-test.js
```

**Output includes:**
- Request rate (requests/sec)
- Response times (p50, p95, p99)
- Error rate
- Data transfer rate

---

## Azure Container Apps Metrics

### View Metrics in Azure Portal

1. Go to: https://portal.azure.com
2. Navigate to: Resource Groups → Your RG → Container Apps → Your App
3. Click on **Metrics** in left menu
4. Add metrics:
   - **Requests** - Total requests
   - **Response Time** - Average response time
   - **CPU Usage** - CPU utilization
   - **Memory Usage** - Memory utilization
   - **Replica Count** - Number of active replicas

### View Metrics via CLI

```bash
# Get replica count
az containerapp replica list \
  --name YOUR-APP \
  --resource-group YOUR-RG

# Get revision traffic
az containerapp revision list \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --query "[].{name:name,trafficWeight:trafficWeight,active:active}"
```

---

## Performance Testing Script

Save as `test-performance.sh`:

```bash
#!/bin/bash

# Performance Testing Script for PraisonAI Service

APP_URL="${1:-https://YOUR-APP.azurecontainerapps.io}"
NUM_REQUESTS="${2:-100}"
CONCURRENCY="${3:-10}"

echo "🚀 Performance Testing: $APP_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Single Request Latency
echo "📊 Test 1: Single Request Latency"
echo "Testing health endpoint..."
for i in {1..5}; do
  time curl -s $APP_URL/health > /dev/null
done
echo ""

# Test 2: Health Endpoint Load Test
echo "📊 Test 2: Health Endpoint Load Test"
echo "Running $NUM_REQUESTS requests with $CONCURRENCY concurrent..."
ab -n $NUM_REQUESTS -c $CONCURRENCY -q $APP_URL/health | grep -E "Requests per second|Time per request|Failed requests"
echo ""

# Test 3: Job Creation Speed
echo "📊 Test 3: Job Creation Speed"
echo "Creating 10 jobs and measuring time..."

START=$(date +%s)
for i in {1..10}; do
  curl -s -X POST $APP_URL/jobs \
    -H "Content-Type: application/json" \
    -d "{\"payload\": {\"title\": \"Perf Test $i\"}}" > /dev/null
done
END=$(date +%s)
DURATION=$((END - START))

echo "Created 10 jobs in ${DURATION}s"
echo "Average: $((DURATION * 100 / 10))ms per job"
echo ""

# Test 4: Job Processing Speed
echo "📊 Test 4: Job Processing Speed"
echo "Creating job and waiting for completion..."

START=$(date +%s)
JOB_ID=$(curl -s -X POST $APP_URL/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "Processing Speed Test"}}' | jq -r '.job_id')

echo "Job ID: $JOB_ID"

# Poll until done
while true; do
  STATUS=$(curl -s $APP_URL/jobs/$JOB_ID | jq -r '.status')
  
  if [ "$STATUS" = "done" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  
  sleep 0.5
done

END=$(date +%s)
DURATION=$((END - START))

echo "Job completed in ${DURATION}s"
echo "Status: $STATUS"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Performance testing complete!"
```

Make it executable:

```bash
chmod +x test-performance.sh

# Run it
./test-performance.sh https://YOUR-APP.azurecontainerapps.io 100 10
```

---

## Monitoring During Load Tests

### Watch Logs in Real-Time

```bash
# Terminal 1: Run load test
ab -n 1000 -c 50 https://YOUR-APP.azurecontainerapps.io/health

# Terminal 2: Watch logs
az containerapp logs show \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --follow
```

### Watch Scaling Events

```bash
# Watch replica count during load test
watch -n 2 "az containerapp replica list \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --query '[].name' -o tsv | wc -l"
```

---

## Expected Performance Benchmarks

### Azure Container Apps (0.5 vCPU, 1GB RAM)

| Metric | Expected Value |
|--------|---------------|
| Health endpoint latency | 50-200ms |
| Job creation latency | 100-300ms |
| Job processing time | 5-15s (depends on job) |
| Requests/sec (health) | 100-500 |
| Requests/sec (jobs) | 50-200 |
| Cold start time | 2-5s |
| Scale-up time | 10-30s |

### Scaling Behavior

- **Min replicas**: 0 (scale to zero)
- **Max replicas**: 3 (configured)
- **Scale trigger**: CPU > 70% or Memory > 80%
- **Scale-up time**: ~10-30 seconds
- **Scale-down time**: ~5 minutes of low load

---

## Optimization Tips

### 1. Increase Resources

```bash
# Update to 1 vCPU, 2GB RAM
az containerapp update \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --cpu 1.0 \
  --memory 2.0Gi
```

### 2. Adjust Scaling Rules

```bash
# Increase max replicas
az containerapp update \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --min-replicas 1 \
  --max-replicas 10
```

### 3. Add HTTP Scaling Rule

```bash
# Scale based on HTTP requests
az containerapp update \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --scale-rule-name http-rule \
  --scale-rule-type http \
  --scale-rule-http-concurrency 50
```

---

## Performance Checklist

- [ ] Test single request latency (< 200ms)
- [ ] Test concurrent requests (100+ req/sec)
- [ ] Test job creation speed (< 300ms)
- [ ] Test job processing time (< 15s)
- [ ] Monitor CPU usage during load (< 80%)
- [ ] Monitor memory usage during load (< 80%)
- [ ] Test auto-scaling (replicas increase under load)
- [ ] Test scale-to-zero (replicas = 0 after 5 min idle)
- [ ] Check error rate (< 1%)
- [ ] Monitor Azure costs during testing

---

## Quick Commands Reference

```bash
# Simple speed test
time curl https://YOUR-APP.azurecontainerapps.io/health

# Load test with ab
ab -n 1000 -c 50 https://YOUR-APP.azurecontainerapps.io/health

# Load test with wrk
wrk -t10 -c100 -d30s https://YOUR-APP.azurecontainerapps.io/health

# Load test with k6
k6 run performance-test.js

# Watch logs
az containerapp logs show --name YOUR-APP --resource-group YOUR-RG --follow

# Check replicas
az containerapp replica list --name YOUR-APP --resource-group YOUR-RG
```

---

## Troubleshooting Performance Issues

### Issue: High Latency (> 1s)

**Possible causes:**
- Cold start (first request after scale-to-zero)
- Insufficient resources
- Network latency

**Solutions:**
```bash
# Set min replicas to 1 (avoid cold starts)
az containerapp update --name YOUR-APP --resource-group YOUR-RG --min-replicas 1

# Increase resources
az containerapp update --name YOUR-APP --resource-group YOUR-RG --cpu 1.0 --memory 2.0Gi
```

### Issue: High Error Rate

**Check logs:**
```bash
az containerapp logs show --name YOUR-APP --resource-group YOUR-RG --tail 100
```

**Common causes:**
- Out of memory
- Timeout errors
- Database connection issues

### Issue: Slow Scaling

**Check scaling configuration:**
```bash
az containerapp show --name YOUR-APP --resource-group YOUR-RG \
  --query properties.template.scale
```

**Adjust scaling:**
```bash
# Faster scale-up
az containerapp update --name YOUR-APP --resource-group YOUR-RG \
  --scale-rule-http-concurrency 30  # Lower threshold = faster scaling
```

---

## Summary

**Quick Performance Test:**
```bash
# 1. Install Apache Bench (comes with macOS)
which ab

# 2. Run load test
ab -n 1000 -c 50 https://YOUR-APP.azurecontainerapps.io/health

# 3. Check results
# Look for: Requests per second, Time per request, Failed requests
```

**Expected Results:**
- Latency: 50-200ms
- Throughput: 100-500 req/sec
- Error rate: < 1%
- Auto-scaling: Yes (under load)

🚀 **Your service is ready for production load testing!**
