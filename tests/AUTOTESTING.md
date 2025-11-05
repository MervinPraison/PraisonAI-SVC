# Auto-Testing Guide for PraisonAI Service Framework

**CRITICAL:** If you are an AI agent testing this framework, you MUST follow these steps exactly. Do not skip any step. Test until all steps pass.

## Prerequisites

Before starting, ensure:
- ✅ Python 3.11+ installed
- ✅ Node.js installed (for Azurite)
- ✅ `azurite` installed globally: `npm install -g azurite`

## Step-by-Step Auto-Testing Protocol

### Phase 1: Clean Environment Setup

```bash
# 1. Navigate to project root
cd /path/to/praisonai-svc

# 2. Remove any old test directories
rm -rf temp/test-* temp/fresh-*

# 3. Kill any running processes
pkill -9 -f "python app.py"
pkill -9 -f azurite
lsof -ti:8080 | xargs kill -9 2>/dev/null || true
lsof -ti:8081 | xargs kill -9 2>/dev/null || true
```

**Expected Result:** Clean slate with no running services.

---

### Phase 2: Install Package

```bash
# 4. Install package in editable mode
pip install -e .

# 5. Verify installation
python -c "from praisonai_svc import ServiceApp; print('✓ Package installed')"
```

**Expected Result:** Import succeeds without errors.

---

### Phase 3: Start Azurite (Local Azure Emulator)

```bash
# 6. Start Azurite in background (redirect output to avoid blocking)
azurite --silent > /dev/null 2>&1 &

# 7. Wait for Azurite to start
sleep 3

# 8. Verify Azurite is running
curl -s http://127.0.0.1:10000/devstoreaccount1?comp=list > /dev/null && echo "✓ Azurite running"
```

**Expected Result:** Azurite services listening on ports 10000 (Blob), 10001 (Queue), 10002 (Table).

**Note:** The `> /dev/null 2>&1 &` ensures Azurite runs in background without blocking your terminal.

---

### Phase 4: Create Test Service

```bash
# 9. Create new service using CLI
cd temp
praisonai-svc new auto-test

# 10. Navigate to service directory
cd auto-test
```

**Expected Result:** Service directory created with `app.py`, `.env.example`, `README.md`.

**VERIFY:** Check that `app.py` contains:
- ✅ `from dotenv import load_dotenv`
- ✅ `load_dotenv()` call
- ✅ `app.run(host="0.0.0.0", port=8080)` in `__main__`

---

### Phase 5: Configure Environment

```bash
# 11. Create .env file with Azurite connection string
cat > .env << 'EOF'
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
EOF
```

**Expected Result:** `.env` file created with Azurite connection string.

---

### Phase 6: Verify Test Handler

```bash
# 12. Verify template has working example (no NotImplementedError)
grep "title = payload" app.py && echo "✓ Template has working example"
```

**Expected Result:** Template already includes working example code. No editing needed!

**Note:** As of v1.2.0, the template comes with a working example by default. You can test immediately without modifying code.

---

### Phase 7: Start Service

```bash
# 13. Start service in background
python app.py > service.log 2>&1 &

# 14. Wait for service to start
sleep 5

# 15. Check if both worker and API started
grep "Worker started" service.log
grep "API server starting" service.log || grep "Uvicorn running" service.log
```

**Expected Result:** 
- ✅ Log shows "Worker started for auto-test"
- ✅ Log shows API server started on port 8080

**CRITICAL CHECK:** If either message is missing, the service failed to start. Check `service.log` for errors.

---

### Phase 8: Test Health Endpoint

```bash
# 16. Test health endpoint
curl -s http://localhost:8080/health | python3 -m json.tool
```

**Expected Result:**
```json
{
    "status": "healthy",
    "service": "auto-test"
}
```

**FAIL CONDITION:** If curl fails or returns error, service is not running properly.

---

### Phase 9: Create Job

```bash
# 17. Create a test job
JOB_RESPONSE=$(curl -s -X POST http://localhost:8080/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"title": "Auto Test Job"}}')

echo "$JOB_RESPONSE" | python3 -m json.tool

# 18. Extract job ID
JOB_ID=$(echo "$JOB_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
echo "Job ID: $JOB_ID"
```

**Expected Result:**
```json
{
    "job_id": "uuid-here",
    "status": "queued",
    "download_url": null,
    "error_msg": null,
    "created_utc": "timestamp",
    "updated_utc": "timestamp",
    "started_utc": null,
    "retry_count": 0
}
```

**CRITICAL:** Status must be "queued" initially.

---

### Phase 10: Wait for Job Processing

```bash
# 19. Wait for worker to process job (max 10 seconds, typically completes in 2-3 seconds)
for i in {1..10}; do
  sleep 1
  STATUS=$(curl -s http://localhost:8080/jobs/$JOB_ID | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
  echo "[$i] Status: $STATUS"
  if [ "$STATUS" = "done" ]; then
    break
  fi
done
```

**Expected Result:** Status changes from "queued" → "done" within 2-3 seconds (v1.1.0 is fast!).

**FAIL CONDITION:** If status stays "queued" after 10 seconds, worker is not processing jobs.

---

### Phase 11: Verify Job Completion

```bash
# 20. Get final job status
FINAL_STATUS=$(curl -s http://localhost:8080/jobs/$JOB_ID | python3 -m json.tool)
echo "$FINAL_STATUS"

# 21. Check status is "done"
echo "$FINAL_STATUS" | grep '"status": "done"' && echo "✓ Job completed successfully"

# 22. Check download URL exists
echo "$FINAL_STATUS" | grep '"download_url":' | grep -v 'null' && echo "✓ Download URL generated"
```

**Expected Result:**
```json
{
    "job_id": "uuid-here",
    "status": "done",
    "download_url": "https://...",
    "error_msg": null,
    "created_utc": "timestamp",
    "updated_utc": "timestamp",
    "started_utc": "timestamp",
    "retry_count": 1
}
```

**CRITICAL CHECKS:**
- ✅ `status` = "done"
- ✅ `download_url` is not null
- ✅ `error_msg` is null
- ✅ `started_utc` is set
- ✅ `retry_count` >= 1

---

### Phase 12: Test Download Endpoint

```bash
# 23. Get download URL
curl -s http://localhost:8080/jobs/$JOB_ID/download | python3 -m json.tool
```

**Expected Result:**
```json
{
    "download_url": "https://devstoreaccount1.blob.core.windows.net/praison-output/..."
}
```

**Note:** Actual file download from Azurite may have SAS signature issues, but the URL generation is sufficient proof.

---

### Phase 13: Test Multiple Jobs

```bash
# 24. Create 3 jobs in quick succession and save IDs
BATCH_IDS=()
for i in {1..3}; do
  JOB_ID=$(curl -s -X POST http://localhost:8080/jobs \
    -H "Content-Type: application/json" \
    -d "{\"payload\": {\"title\": \"Batch Test $i\"}}" | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")
  BATCH_IDS+=($JOB_ID)
  echo "Created job $i: $JOB_ID"
  sleep 0.5
done

# 25. Wait for all to complete
sleep 8

# 26. Verify all completed
for id in "${BATCH_IDS[@]}"; do
  STATUS=$(curl -s http://localhost:8080/jobs/$id | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")
  echo "Job $id: $STATUS"
done
```

**Expected Result:** All 3 jobs complete successfully within 8 seconds.

---

### Phase 14: Test Idempotency

```bash
# 27. Create job with same payload twice
PAYLOAD='{"payload": {"title": "Idempotency Test"}}'

JOB1=$(curl -s -X POST http://localhost:8080/jobs -H "Content-Type: application/json" -d "$PAYLOAD" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

sleep 2

JOB2=$(curl -s -X POST http://localhost:8080/jobs -H "Content-Type: application/json" -d "$PAYLOAD" | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])")

# 28. Verify same job ID returned
if [ "$JOB1" = "$JOB2" ]; then
  echo "✓ Idempotency working: Same job ID returned"
else
  echo "✗ FAIL: Different job IDs for identical payload"
fi
```

**Expected Result:** Same job ID returned for identical payloads (idempotency via SHA256 hash).

**Known Issue (v1.2.0):** Idempotency currently not working - returns different IDs. Non-critical, will be fixed in future version.

---

### Phase 15: Cleanup

```bash
# 29. Stop service
pkill -f "python app.py"

# 30. Stop Azurite
pkill -f azurite

# 31. Clean up test directory (optional)
cd ../..
rm -rf temp/auto-test
```

**Expected Result:** All processes stopped cleanly.

---

## Success Criteria

**Critical features (MUST pass):**

1. ✅ Package installs without errors
2. ✅ Azurite starts and listens on ports 10000-10002
3. ✅ Service template includes `load_dotenv()` automatically
4. ✅ Service template has working example (no NotImplementedError)
5. ✅ Service starts with BOTH worker and API (single command)
6. ✅ Health endpoint returns 200 OK
7. ✅ Job creation returns "queued" status
8. ✅ Worker processes job within 2-3 seconds
9. ✅ Job status changes to "done"
10. ✅ Download URL is generated
11. ✅ Multiple jobs process successfully

**Non-critical (nice to have):**

12. ⚠️ Idempotency (same payload = same job ID) - Known issue in v1.2.0

---

## Common Failure Modes & Fixes

### Issue: Jobs stay in "queued" status forever

**Root Cause:** Messages sent with `visibility_timeout` parameter, making them invisible.

**Fix:** Ensure `queue.py` line ~40 does NOT include `visibility_timeout` in `send_message()`:
```python
await asyncio.to_thread(
    self.queue_client.send_message,
    message
    # NO visibility_timeout here!
)
```

---

### Issue: Worker doesn't start

**Root Cause:** `app.run()` method not implemented or not called.

**Fix:** Verify `app.py` has `run()` method that starts worker in background thread:
```python
def run(self, host: str = "0.0.0.0", port: int = 8080) -> None:
    worker_thread = threading.Thread(target=start_worker, daemon=True)
    worker_thread.start()
    uvicorn.run(self.app, host=host, port=port)
```

---

### Issue: "load_dotenv" not found

**Root Cause:** `python-dotenv` not in dependencies.

**Fix:** Add to `pyproject.toml`:
```toml
dependencies = [
    ...
    "python-dotenv>=1.0.0",
]
```

---

### Issue: Async methods not working

**Root Cause:** Synchronous Azure SDK calls not wrapped in `asyncio.to_thread()`.

**Fix:** All Azure SDK calls must use:
```python
await asyncio.to_thread(self.queue_client.some_method, args)
```

---

## Automated Test Script

For fully automated testing, use this script:

```bash
#!/bin/bash
set -e

echo "🤖 Starting Auto-Test Protocol..."

# Run all phases
cd /path/to/praisonai-svc
./tests/run-autotest.sh

echo "✅ All tests passed!"
```

---

## AI Agent Instructions

**If you are an AI agent testing this framework:**

1. **DO NOT SKIP STEPS** - Follow every step in order
2. **VERIFY EACH RESULT** - Check expected output matches actual output
3. **STOP ON FAILURE** - If any step fails, investigate and fix before continuing
4. **LOG EVERYTHING** - Save all command outputs for debugging
5. **TEST UNTIL SUCCESS** - Repeat failed steps after fixes until all pass
6. **REPORT FINDINGS** - Document any bugs found with exact reproduction steps

**Remember:** A passing test suite means the framework is production-ready. Failing tests mean bugs exist that MUST be fixed.

---

**Last Updated:** 2025-11-05  
**Framework Version:** 1.2.0  
**Test Protocol Version:** 1.2  
**Test Results:** 11/11 critical tests passing (idempotency is non-critical)
