#!/bin/bash

# Performance Testing Script for PraisonAI Service
# Usage: ./test-performance.sh [APP_URL] [NUM_REQUESTS] [CONCURRENCY]
#
# If APP_URL is not provided, will automatically detect from check-azure.sh

set -e

# Check if first argument is a URL (starts with http)
if [[ "$1" =~ ^https?:// ]]; then
    APP_URL="${1}"
    NUM_REQUESTS="${2:-100}"
    CONCURRENCY="${3:-10}"
else
    APP_URL=""
    NUM_REQUESTS="${1:-100}"
    CONCURRENCY="${2:-10}"
fi

# Auto-detect APP_URL if not provided
if [ -z "$APP_URL" ]; then
    echo "🔍 No APP_URL provided. Auto-detecting from Azure..."
    echo ""
    
    # Find check-azure.sh script
    CHECK_SCRIPT="../check-azure.sh"
    if [ ! -f "$CHECK_SCRIPT" ]; then
        CHECK_SCRIPT="./check-azure.sh"
    fi
    
    if [ ! -f "$CHECK_SCRIPT" ]; then
        echo "❌ Error: check-azure.sh not found"
        echo ""
        echo "Please provide APP_URL manually:"
        echo "  $0 <APP_URL> [NUM_REQUESTS] [CONCURRENCY]"
        echo ""
        echo "Example:"
        echo "  $0 https://my-service.azurecontainerapps.io 100 10"
        exit 1
    fi
    
    # Run check-azure.sh and extract URL
    TEMP_OUTPUT=$(mktemp)
    bash "$CHECK_SCRIPT" > "$TEMP_OUTPUT" 2>&1
    
    # Extract the first container app URL
    APP_URL=$(grep "URL:" "$TEMP_OUTPUT" | head -1 | awk '{print $2}')
    
    rm -f "$TEMP_OUTPUT"
    
    if [ -z "$APP_URL" ]; then
        echo "❌ No deployed container apps found"
        echo ""
        echo "Please deploy a service first or provide APP_URL manually:"
        echo "  $0 <APP_URL> [NUM_REQUESTS] [CONCURRENCY]"
        exit 1
    fi
    
    echo "✅ Auto-detected service URL: $APP_URL"
    echo ""
fi

# Remove trailing slash
APP_URL="${APP_URL%/}"

echo "🚀 Performance Testing"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "URL: $APP_URL"
echo "Requests: $NUM_REQUESTS"
echo "Concurrency: $CONCURRENCY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if tools are installed
if ! command -v curl &> /dev/null; then
    echo "❌ curl not found. Please install curl."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "⚠️  jq not found. Installing jq for JSON parsing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install jq
    else
        echo "Please install jq: sudo apt-get install jq"
        exit 1
    fi
fi

# Test 1: Connection Test
echo "📊 Test 1: Connection Test"
echo "Testing if service is reachable..."
if curl -s -f -o /dev/null -w "%{http_code}" $APP_URL/health | grep -q "200"; then
    echo "✅ Service is reachable"
else
    echo "❌ Service is not reachable. Check URL and try again."
    exit 1
fi
echo ""

# Test 2: Single Request Latency
echo "📊 Test 2: Single Request Latency (5 samples)"
echo "Testing health endpoint response time..."
TOTAL_TIME=0
for i in {1..5}; do
    START=$(date +%s%N)
    curl -s $APP_URL/health > /dev/null
    END=$(date +%s%N)
    DURATION=$(( (END - START) / 1000000 ))
    echo "  Request $i: ${DURATION}ms"
    TOTAL_TIME=$((TOTAL_TIME + DURATION))
done
AVG_TIME=$((TOTAL_TIME / 5))
echo "  Average: ${AVG_TIME}ms"
echo ""

# Test 3: Load Test with curl (if ab not available)
echo "📊 Test 3: Concurrent Request Test"
if command -v ab &> /dev/null; then
    echo "Using Apache Bench (ab)..."
    echo "Running $NUM_REQUESTS requests with $CONCURRENCY concurrent connections..."
    ab -n $NUM_REQUESTS -c $CONCURRENCY -q $APP_URL/health 2>&1 | grep -E "Requests per second|Time per request|Failed requests|Complete requests"
else
    echo "Apache Bench not found. Using curl for basic test..."
    echo "Running $NUM_REQUESTS sequential requests..."
    
    START=$(date +%s)
    SUCCESS=0
    FAILED=0
    
    for i in $(seq 1 $NUM_REQUESTS); do
        if curl -s -f $APP_URL/health > /dev/null 2>&1; then
            SUCCESS=$((SUCCESS + 1))
        else
            FAILED=$((FAILED + 1))
        fi
        
        # Show progress every 10 requests
        if [ $((i % 10)) -eq 0 ]; then
            echo "  Progress: $i/$NUM_REQUESTS"
        fi
    done
    
    END=$(date +%s)
    DURATION=$((END - START))
    RPS=$((NUM_REQUESTS / DURATION))
    
    echo "  Complete requests: $SUCCESS"
    echo "  Failed requests: $FAILED"
    echo "  Total time: ${DURATION}s"
    echo "  Requests per second: ${RPS}"
fi
echo ""

# Test 4: Job Creation Speed
echo "📊 Test 4: Job Creation Speed"
echo "Creating 10 jobs and measuring time..."

START=$(date +%s%N)
JOB_IDS=()

for i in {1..10}; do
    RESPONSE=$(curl -s -X POST $APP_URL/jobs \
        -H "Content-Type: application/json" \
        -d "{\"payload\": {\"title\": \"Perf Test $i\"}}")
    
    JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
    JOB_IDS+=($JOB_ID)
    
    if [ $((i % 5)) -eq 0 ]; then
        echo "  Created $i/10 jobs..."
    fi
done

END=$(date +%s%N)
DURATION=$(( (END - START) / 1000000 ))

echo "  Created 10 jobs in ${DURATION}ms"
echo "  Average: $((DURATION / 10))ms per job"
echo ""

# Test 5: Job Processing Speed
echo "📊 Test 5: Job Processing Speed"
echo "Creating job and waiting for completion..."

START=$(date +%s)
JOB_RESPONSE=$(curl -s -X POST $APP_URL/jobs \
    -H "Content-Type: application/json" \
    -d '{"payload": {"title": "Processing Speed Test"}}')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')
echo "  Job ID: $JOB_ID"

# Poll until done (max 60 seconds)
MAX_WAIT=60
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS=$(curl -s $APP_URL/jobs/$JOB_ID | jq -r '.status')
    
    if [ "$STATUS" = "done" ]; then
        echo "  ✅ Job completed successfully"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "  ❌ Job failed"
        break
    fi
    
    sleep 1
    ELAPSED=$((ELAPSED + 1))
    
    if [ $((ELAPSED % 5)) -eq 0 ]; then
        echo "  Status: $STATUS (${ELAPSED}s elapsed)"
    fi
done

END=$(date +%s)
DURATION=$((END - START))

echo "  Processing time: ${DURATION}s"
echo "  Final status: $STATUS"
echo ""

# Test 6: Error Rate Test
echo "📊 Test 6: Error Rate Test"
echo "Testing error handling with 20 rapid requests..."

SUCCESS=0
FAILED=0

for i in {1..20}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $APP_URL/health)
    
    if [ "$HTTP_CODE" = "200" ]; then
        SUCCESS=$((SUCCESS + 1))
    else
        FAILED=$((FAILED + 1))
    fi
done

ERROR_RATE=$(awk "BEGIN {print ($FAILED / 20) * 100}")

echo "  Success: $SUCCESS/20"
echo "  Failed: $FAILED/20"
echo "  Error rate: ${ERROR_RATE}%"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Performance Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Single Request Latency: ${AVG_TIME}ms"
echo "✅ Job Creation Speed: $((DURATION / 10))ms per job"
echo "✅ Job Processing Time: ${DURATION}s"
echo "✅ Error Rate: ${ERROR_RATE}%"
echo ""

# Performance rating
if [ $AVG_TIME -lt 200 ] && [ $(echo "$ERROR_RATE < 1" | bc -l) -eq 1 ]; then
    echo "🎉 Performance: EXCELLENT"
elif [ $AVG_TIME -lt 500 ] && [ $(echo "$ERROR_RATE < 5" | bc -l) -eq 1 ]; then
    echo "✅ Performance: GOOD"
else
    echo "⚠️  Performance: NEEDS IMPROVEMENT"
    echo ""
    echo "Recommendations:"
    if [ $AVG_TIME -gt 500 ]; then
        echo "  - High latency detected. Consider increasing resources."
    fi
    if [ $(echo "$ERROR_RATE > 1" | bc -l) -eq 1 ]; then
        echo "  - High error rate. Check logs for issues."
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Performance testing complete!"
echo ""
echo "Next steps:"
echo "  - View logs: az containerapp logs show --name YOUR-APP --resource-group YOUR-RG --follow"
echo "  - Check metrics in Azure Portal"
echo "  - Run load test: ab -n 1000 -c 50 $APP_URL/health"
echo ""
