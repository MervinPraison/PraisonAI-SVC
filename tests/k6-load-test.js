import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const jobCreationTime = new Trend('job_creation_time');
const jobProcessingTime = new Trend('job_processing_time');
const jobsCreated = new Counter('jobs_created');
const jobsCompleted = new Counter('jobs_completed');

// Test configuration
export const options = {
  stages: [
    { duration: '10s', target: 5 },    // Warm up: 5 users
    { duration: '20s', target: 10 },   // Ramp up: 10 users
    { duration: '20s', target: 20 },   // Peak load: 20 users
    { duration: '10s', target: 0 },    // Ramp down: 0 users
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000'],     // 95% of requests should be below 1s
    'http_req_failed': ['rate<0.05'],        // Less than 5% of requests should fail
    'errors': ['rate<0.05'],                 // Less than 5% error rate
    'job_creation_time': ['p(95)<500'],      // 95% of job creations should be below 500ms
    'checks': ['rate>0.95'],                 // 95% of checks should pass
  },
};

// Configuration - UPDATE THIS WITH YOUR SERVICE URL
const BASE_URL = __ENV.BASE_URL || 'https://YOUR-APP.azurecontainerapps.io';

export default function () {
  // Test 1: Health Check
  const healthRes = http.get(`${BASE_URL}/health`);
  
  const healthCheck = check(healthRes, {
    'health status is 200': (r) => r.status === 200,
    'health response time < 500ms': (r) => r.timings.duration < 500,
    'health has status field': (r) => {
      try {
        return JSON.parse(r.body).status === 'healthy';
      } catch (e) {
        return false;
      }
    },
  });
  
  errorRate.add(!healthCheck);
  sleep(1);

  // Test 2: Create Job
  const jobPayload = JSON.stringify({
    payload: {
      title: `k6 Load Test - User ${__VU} - Iteration ${__ITER}`,
      description: 'Performance testing with k6',
      timestamp: new Date().toISOString(),
    }
  });
  
  const jobStartTime = Date.now();
  const jobRes = http.post(`${BASE_URL}/jobs`, jobPayload, {
    headers: { 'Content-Type': 'application/json' },
  });
  const jobEndTime = Date.now();
  
  const jobCheck = check(jobRes, {
    'job creation status is 200': (r) => r.status === 200,
    'job has job_id': (r) => {
      try {
        return JSON.parse(r.body).job_id !== undefined;
      } catch (e) {
        return false;
      }
    },
    'job status is queued': (r) => {
      try {
        return JSON.parse(r.body).status === 'queued';
      } catch (e) {
        return false;
      }
    },
  });
  
  errorRate.add(!jobCheck);
  jobCreationTime.add(jobEndTime - jobStartTime);
  
  if (jobCheck) {
    jobsCreated.add(1);
  }

  // Test 3: Check Job Status (only for successful job creations)
  if (jobRes.status === 200) {
    let jobId;
    try {
      jobId = JSON.parse(jobRes.body).job_id;
    } catch (e) {
      errorRate.add(1);
      sleep(2);
      return;
    }
    
    sleep(1);
    
    const statusRes = http.get(`${BASE_URL}/jobs/${jobId}`);
    const statusCheck = check(statusRes, {
      'status check is 200': (r) => r.status === 200,
      'status response has job_id': (r) => {
        try {
          return JSON.parse(r.body).job_id === jobId;
        } catch (e) {
          return false;
        }
      },
    });
    
    errorRate.add(!statusCheck);
    
    // Optional: Wait for job completion (only for a subset of users to avoid overload)
    if (__VU % 10 === 0) {  // Only 10% of users wait for completion
      const processingStartTime = Date.now();
      let attempts = 0;
      const maxAttempts = 30;  // Max 30 seconds
      
      while (attempts < maxAttempts) {
        sleep(1);
        attempts++;
        
        const pollRes = http.get(`${BASE_URL}/jobs/${jobId}`);
        if (pollRes.status === 200) {
          try {
            const status = JSON.parse(pollRes.body).status;
            if (status === 'done' || status === 'failed') {
              const processingEndTime = Date.now();
              jobProcessingTime.add(processingEndTime - processingStartTime);
              
              if (status === 'done') {
                jobsCompleted.add(1);
              }
              break;
            }
          } catch (e) {
            errorRate.add(1);
            break;
          }
        }
      }
    }
  }

  sleep(2);
}

// Setup function (runs once at the start)
export function setup() {
  console.log(`Starting load test against: ${BASE_URL}`);
  
  // Verify service is reachable
  const res = http.get(`${BASE_URL}/health`);
  if (res.status !== 200) {
    throw new Error(`Service not reachable. Status: ${res.status}`);
  }
  
  console.log('Service is reachable. Starting test...');
  return { startTime: Date.now() };
}

// Teardown function (runs once at the end)
export function teardown(data) {
  const endTime = Date.now();
  const duration = (endTime - data.startTime) / 1000;
  console.log(`Test completed in ${duration}s`);
}

// Handle summary (custom summary output)
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'performance-report.json': JSON.stringify(data),
  };
}

function textSummary(data, options) {
  const indent = options.indent || '';
  const enableColors = options.enableColors || false;
  
  let summary = '\n';
  summary += `${indent}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
  summary += `${indent}📊 Performance Test Summary\n`;
  summary += `${indent}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
  
  // HTTP metrics
  if (data.metrics.http_reqs) {
    summary += `${indent}HTTP Requests:\n`;
    summary += `${indent}  Total: ${data.metrics.http_reqs.values.count}\n`;
    summary += `${indent}  Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)}/s\n\n`;
  }
  
  // Response time
  if (data.metrics.http_req_duration) {
    summary += `${indent}Response Time:\n`;
    summary += `${indent}  Average: ${(data.metrics.http_req_duration.values.avg || 0).toFixed(2)}ms\n`;
    summary += `${indent}  Median: ${(data.metrics.http_req_duration.values.med || 0).toFixed(2)}ms\n`;
    summary += `${indent}  95th percentile: ${(data.metrics.http_req_duration.values['p(95)'] || 0).toFixed(2)}ms\n`;
    if (data.metrics.http_req_duration.values['p(99)']) {
      summary += `${indent}  99th percentile: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
    }
    summary += `\n`;
  }
  
  // Custom metrics
  if (data.metrics.jobs_created) {
    summary += `${indent}Jobs:\n`;
    summary += `${indent}  Created: ${data.metrics.jobs_created.values.count}\n`;
    if (data.metrics.jobs_completed) {
      summary += `${indent}  Completed: ${data.metrics.jobs_completed.values.count}\n`;
    }
    summary += `\n`;
  }
  
  // Error rate
  if (data.metrics.errors) {
    const errorPct = (data.metrics.errors.values.rate * 100).toFixed(2);
    summary += `${indent}Error Rate: ${errorPct}%\n\n`;
  }
  
  summary += `${indent}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
  
  return summary;
}
