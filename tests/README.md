# Testing Guide

Complete guide for testing your PraisonAI services - local development, performance testing, and load testing.

---

## 📁 Test Files in This Directory

| File | Purpose |
|------|---------|
| **README.md** | This file - complete testing guide |
| **AUTOTESTING.md** | Manual testing protocol for local development |
| **test-performance.sh** | Automated performance testing script |
| **PERFORMANCE.md** | Detailed performance testing guide |
| **k6-load-test.js** | Advanced k6 load testing script |

---

## 🚀 Quick Start

### Step 1: Find Your Service URL

```bash
# Run the check script to find your deployed services
cd /path/to/praisonai-svc
./check-azure.sh
```

**Output shows your deployed apps:**
```
5️⃣  Deployed Container Apps
   ✅ FOUND:
      - my-service (Resource Group: my-rg)
        URL: https://my-service.randomstring.eastus.azurecontainerapps.io
        Status: Running
```

**Copy the URL and set it:**
```bash
export APP_URL="https://my-service.randomstring.eastus.azurecontainerapps.io"
```

### Step 2: Run Performance Test

**Option A: Auto-detect (Recommended)**
```bash
cd tests
./test-performance.sh

# With custom settings
./test-performance.sh 100 10  # 100 requests, 10 concurrent
```

**Option B: Specify URL manually**
```bash
cd tests
./test-performance.sh $APP_URL

# With custom settings
./test-performance.sh $APP_URL 100 10
```

---

## 🧪 Testing Tools

### 1. Automated Performance Test (Recommended)

**Best for:** Quick comprehensive overview

```bash
cd tests
# Auto-detect service URL
./test-performance.sh

# Or specify URL manually
./test-performance.sh $APP_URL

# With custom settings
./test-performance.sh 100 10  # 100 requests, 10 concurrent
```

**What it tests:**
- ✅ Connection test
- ✅ Single request latency (5 samples)
- ✅ Concurrent requests
- ✅ Job creation speed
- ✅ Job processing time
- ✅ Error rate
- ✅ Performance rating

**Example output:**
```
📊 Performance Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Single Request Latency: 286ms
✅ Job Creation Speed: 324ms per job
✅ Job Processing Time: 22s
✅ Error Rate: 0%

✅ Performance: GOOD
```

### 2. Apache Bench (ab)

**Best for:** Quick load testing

```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 $APP_URL/health

# 1000 requests, 50 concurrent
ab -n 1000 -c 50 $APP_URL/health

# POST requests (job creation)
cat > job.json << 'EOF'
{"payload": {"title": "Load Test"}}
EOF

ab -n 50 -c 5 -p job.json -T application/json $APP_URL/jobs
```

**Key metrics:**
- `Requests per second` - Throughput
- `Time per request` - Latency
- `Failed requests` - Should be 0

### 3. wrk

**Best for:** High-performance load testing

```bash
# Install (if not already)
brew install wrk

# 4 threads, 10 connections, 10 seconds
wrk -t4 -c10 -d10s $APP_URL/health

# 10 threads, 100 connections, 30 seconds
wrk -t10 -c100 -d30s $APP_URL/health

# With custom script for POST requests
cat > wrk-post.lua << 'EOF'
wrk.method = "POST"
wrk.headers["Content-Type"] = "application/json"
wrk.body = '{"payload": {"title": "wrk test"}}'
EOF

wrk -t4 -c10 -d10s -s wrk-post.lua $APP_URL/jobs
```

**Output:**
- `Latency` - Response time distribution
- `Req/Sec` - Requests per second per thread
- `Requests/sec` - Total throughput

### 4. k6 (Advanced)

**Best for:** Advanced load testing with scenarios

```bash
# Install (if not already)
brew install k6

# Run test
cd tests
k6 run -e BASE_URL=$APP_URL k6-load-test.js

# Quick test (30 seconds, 10 users)
k6 run --duration 30s --vus 10 -e BASE_URL=$APP_URL k6-load-test.js

# Stress test (100 users)
k6 run --vus 100 --duration 1m -e BASE_URL=$APP_URL k6-load-test.js

# Output to JSON
k6 run -e BASE_URL=$APP_URL k6-load-test.js --out json=results.json
```

**Features:**
- ✅ Gradual load ramping
- ✅ Custom metrics (job creation time, processing time)
- ✅ Thresholds & assertions
- ✅ Detailed performance reports

### 5. curl (Simple Tests)

**Best for:** Quick manual testing

```bash
# Health check
curl $APP_URL/health

# Health check with timing
time curl $APP_URL/health

# Create job
curl -X POST $APP_URL/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "Test Job"}}'

# Check job status
JOB_ID="your-job-id"
curl $APP_URL/jobs/$JOB_ID

# Pretty print JSON
curl -s $APP_URL/health | jq
```

---

## 📊 Performance Benchmarks

### Expected Performance (0.5 vCPU, 1GB RAM)

| Metric | Excellent | Good | Needs Work |
|--------|-----------|------|------------|
| Latency | < 100ms | 100-300ms | > 300ms |
| Throughput | > 100 req/s | 50-100 req/s | < 50 req/s |
| Error Rate | 0% | < 1% | > 1% |
| Job Processing | < 10s | 10-30s | > 30s |

### Tool Comparison

| Tool | Best For | Pros | Cons |
|------|----------|------|------|
| **test-performance.sh** | Complete overview | All-in-one, easy | Basic metrics |
| **ab** | Quick tests | Simple, fast | Limited features |
| **wrk** | High load | Very fast, efficient | Less detailed output |
| **k6** | Advanced testing | Feature-rich, scriptable | More complex |
| **curl** | Manual testing | Universal, simple | One request at a time |

---

## 🔍 Monitoring

### Azure Logs

```bash
# Stream logs
az containerapp logs show \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --follow

# Last 100 lines
az containerapp logs show \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --tail 100
```

### Replica Count

```bash
# List replicas
az containerapp replica list \
  --name YOUR-APP \
  --resource-group YOUR-RG

# Watch replica count (updates every 2 seconds)
watch -n 2 "az containerapp replica list \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --query '[].name' -o tsv | wc -l"
```

### App Status

```bash
# Get running status
az containerapp show \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --query properties.runningStatus

# Get app URL
az containerapp show \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --query properties.configuration.ingress.fqdn -o tsv
```

---

## 🎯 Common Test Scenarios

### 1. Baseline Test
```bash
# Establish baseline performance
cd tests
./test-performance.sh $APP_URL > baseline.txt
cat baseline.txt
```

### 2. Load Test
```bash
# Test with moderate load
ab -n 1000 -c 50 $APP_URL/health
```

### 3. Stress Test
```bash
# Test with high load
wrk -t10 -c100 -d30s $APP_URL/health
```

### 4. Endurance Test
```bash
# Test sustained load (5 minutes)
cd tests
k6 run --duration 5m --vus 50 -e BASE_URL=$APP_URL k6-load-test.js
```

### 5. Spike Test
```bash
# Test sudden traffic spike
cd tests
k6 run --stage 10s:10,5s:100,10s:10 -e BASE_URL=$APP_URL k6-load-test.js
```

---

## 🔧 Troubleshooting

### High Latency (> 500ms)

**Check logs:**
```bash
az containerapp logs show --name YOUR-APP --resource-group YOUR-RG --tail 100
```

**Solutions:**
```bash
# Increase resources
az containerapp update \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --cpu 1.0 \
  --memory 2.0Gi

# Avoid cold starts (set min replicas)
az containerapp update \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --min-replicas 1
```

### High Error Rate (> 1%)

**Check error logs:**
```bash
az containerapp logs show --name YOUR-APP --resource-group YOUR-RG | grep ERROR
```

**Common causes:**
- Out of memory
- Timeout errors
- Database/storage connection issues

**Check replica health:**
```bash
az containerapp replica list --name YOUR-APP --resource-group YOUR-RG
```

### Slow Scaling

**Check current scaling config:**
```bash
az containerapp show --name YOUR-APP --resource-group YOUR-RG \
  --query properties.template.scale
```

**Adjust scaling threshold:**
```bash
# Lower threshold = faster scaling
az containerapp update \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --scale-rule-http-concurrency 30
```

---

## 📝 One-Liners

```bash
# Find your service URL
../check-azure.sh | grep "URL:"

# Quick health check
curl -s $APP_URL/health | jq

# 100 requests benchmark
ab -n 100 -c 10 -q $APP_URL/health | grep "Requests per second"

# 10-second load test
wrk -t4 -c10 -d10s $APP_URL/health

# Watch logs live
az containerapp logs show --name YOUR-APP --resource-group YOUR-RG --follow

# Count active replicas
az containerapp replica list --name YOUR-APP --resource-group YOUR-RG --query '[].name' -o tsv | wc -l

# Full performance test
cd tests && ./test-performance.sh $APP_URL
```

---

## 💡 Best Practices

1. ✅ **Find your URL first** - Run `../check-azure.sh` to get your service URL
2. ✅ **Test locally first** - Before deploying to Azure
3. ✅ **Establish baseline** - Record initial performance metrics
4. ✅ **Test regularly** - Weekly performance checks
5. ✅ **Start small** - Begin with low load, increase gradually
6. ✅ **Monitor during tests** - Watch logs and replica count
7. ✅ **Check error rates** - Should be < 1%
8. ✅ **Verify scaling** - Ensure auto-scaling works under load
9. ✅ **Document results** - Keep performance history
10. ✅ **Cost awareness** - Monitor Azure spending during tests

---

## 🚀 Quick Command Reference

### Get Your Service URL
```bash
# Run check script
cd /path/to/praisonai-svc
./check-azure.sh

# Or use Azure CLI
az containerapp show \
  --name YOUR-APP \
  --resource-group YOUR-RG \
  --query properties.configuration.ingress.fqdn -o tsv

# Set environment variable
export APP_URL="https://YOUR-APP.azurecontainerapps.io"
```

### Run Tests
```bash
# Complete automated test
cd tests
./test-performance.sh $APP_URL

# Quick load test
ab -n 1000 -c 50 $APP_URL/health

# High-performance test
wrk -t10 -c100 -d30s $APP_URL/health

# Advanced test
cd tests
k6 run -e BASE_URL=$APP_URL k6-load-test.js
```

### Monitor
```bash
# Stream logs
az containerapp logs show --name YOUR-APP --resource-group YOUR-RG --follow

# Check replicas
az containerapp replica list --name YOUR-APP --resource-group YOUR-RG

# View metrics in portal
open https://portal.azure.com
```

---

## 📚 Additional Resources

- **AUTOTESTING.md** - Manual local testing protocol
- **PERFORMANCE.md** - Detailed performance testing guide
- **k6-load-test.js** - Advanced k6 test script
- **../DEPLOYMENT.md** - Azure deployment guide
- **../check-azure.sh** - Find existing Azure resources

---

## 📞 Support

- **GitHub Issues**: https://github.com/MervinPraison/PraisonAI-SVC/issues
- **Azure Docs**: https://learn.microsoft.com/azure/container-apps/

---

## Summary

**Quick Test (Auto-detect):**
```bash
cd tests
./test-performance.sh
```

**Or with manual URL:**
```bash
# 1. Find your service URL
cd /path/to/praisonai-svc && ./check-azure.sh

# 2. Set environment variable
export APP_URL="https://YOUR-APP.azurecontainerapps.io"

# 3. Run performance test
cd tests && ./test-performance.sh $APP_URL
```

**4. Monitor:**
```bash
az containerapp logs show --name YOUR-APP --resource-group YOUR-RG --follow
```

🚀 **Happy Testing!**
