# 🧩 Product Requirements Document (PRD)

## 1. Product Overview

**Product Name:** PraisonAI Service Framework — *Azure Minimal Edition*
**Objective:**
A unified framework (`praisonai-svc`) that turns any PraisonAI Python package into a web service on **Azure** using just **one file per package**, with predictable cost and simple deployment.

**Goal:**
Run all PraisonAI generators (e.g., PraisonAIPPT, PraisonAIVideo, PraisonAIWP) as lightweight, scalable micro-services inside **Azure Container Apps**, using only **cheap storage-based components** — no Redis, no expensive Service Bus.

---

## 2. Key Design Goals

| # | Goal                      | Explanation                                                              |
| - | ------------------------- | ------------------------------------------------------------------------ |
| 1 | One-file service creation | Only a `handlers.py` file per new package.                               |
| 2 | Minimal Azure footprint   | Uses only ACA + Blob + Storage Queue + Table Storage.                    |
| 3 | Cost-predictable          | Scale-to-zero, hard-capped replicas, no hidden meters.                   |
| 4 | WP-native UI              | WordPress chatbot directly posts YAML/JSON to the API (no PHP blocking). |
| 5 | Fully serverless          | No VM, no Kubernetes, no Redis.                                          |
| 6 | Quick deploy CLI          | `praisonai-svc deploy azure` builds and deploys automatically.           |

---

## 3. System Architecture

### 3.1 Core Components (Minimal Set)

| Component        | Technology                                            | Purpose                                                      |
| ---------------- | ----------------------------------------------------- | ------------------------------------------------------------ |
| **API / Worker** | Azure Container App (FastAPI + Worker Container)      | Handles requests, validates input, triggers background jobs. |
| **Queue**        | Azure Storage Queue                                   | Holds job messages for asynchronous processing.              |
| **Storage**      | Azure Blob Storage                                    | Stores generated `.pptx`, `.pdf`, or `.docx` files.          |
| **Job State**    | Azure Table Storage                                   | Tracks job ID → status/download URL.                         |
| **Monitoring**   | Basic Container App logs + App Insights (sampling on) | Observability and alerting.                                  |
| **Frontend**     | WordPress chatbot (UI)                                | User-facing chat interface that triggers the API.            |
| **CLI**          | `praisonai-svc`                                       | Local run, test, and Azure deploy commands.                  |

---

### 3.2 Workflow Sequence

1. User sends YAML/JSON from chatbot (in WordPress) → `POST /jobs`.
2. FastAPI validates and stores `{job_id, status: "queued"}` in **Table Storage**.
3. API pushes a small JSON message to **Storage Queue**.
4. The **Worker container** polls the queue, pops a message, runs your handler (`build_ppt`, etc.).
5. Worker uploads the generated file to **Blob Storage** and updates the corresponding Table Storage row with `{status:"done", download_url:"SAS_URL"}`.
6. Frontend polls `GET /jobs/{id}` every few seconds.
7. Once ready, user downloads directly from the signed Blob URL (no PHP proxy).

---

## 4. Technical Implementation

### 4.1 Base SDK (`praisonai-svc`)

**Responsibilities**

* FastAPI app factory
* `/jobs` endpoints
* YAML/JSON parsing
* Queue push/poll helpers (Storage Queue)
* Blob upload + SAS signing
* Table Storage job state tracking
* CLI commands (`run`, `deploy`, `new`)

---

### 4.2 Package Security & Defensive Registration

**Package Name:** `praisonai-svc`

**Rationale:**
- Matches CLI tool name (`praisonai-svc`)
- Clear "service" meaning
- Consistent with PraisonAI ecosystem
- Standard Python convention (hyphen in package, underscore in imports)

**Typosquatting Risk:**

PyPI package name squatting is a real security threat. Attackers register similar names to:
- Capture accidental installs
- Distribute malware
- Phish credentials
- Damage brand reputation

**Defensive Strategy:**

To protect users and the PraisonAI brand, register **all common variations** as defensive placeholder packages:

| Defensive Package | Purpose | Auto-Install |
|-------------------|---------|--------------|
| `praisonaisvc` | No hyphen variant | → `praisonai-svc` |
| `praisonai_svc` | Underscore variant | → `praisonai-svc` |
| `praisonai-service` | Full word variant | → `praisonai-svc` |
| `praisonai-svcs` | Plural variant | → `praisonai-svc` |

**Defensive Package Template:**

```python
# defensive-packages/praisonaisvc/setup.py
from setuptools import setup

setup(
    name="praisonaisvc",
    version="0.0.1",
    description="⚠️ TYPO - Install 'praisonai-svc' instead",
    long_description="""
    # Wrong Package!
    
    You probably meant to install **praisonai-svc** (with hyphen).
    
    This is a defensive package to prevent typosquatting.
    The correct package will be installed automatically.
    
    ## Correct Installation:
    ```bash
    pip install praisonai-svc
    ```
    
    See: https://github.com/MervinPraison/PraisonAI-SVC
    """,
    long_description_content_type="text/markdown",
    install_requires=["praisonai-svc>=1.0.0"],  # Auto-installs correct package
    author="MervinPraison",
    url="https://github.com/MervinPraison/PraisonAI-SVC",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.8",
)
```

**Deployment Checklist:**

- [ ] Register main package: `praisonai-svc`
- [ ] Enable PyPI 2FA on account
- [ ] Register defensive package: `praisonaisvc`
- [ ] Register defensive package: `praisonai_svc`
- [ ] Register defensive package: `praisonai-service`
- [ ] Register defensive package: `praisonai-svcs`
- [ ] Add security policy to README
- [ ] Monitor PyPI for similar names (quarterly)
- [ ] Set up GitHub security alerts

**Security Policy (README.md):**

```markdown
## Security

### Official Package
The only official package is: **praisonai-svc**

Install via:
```bash
pip install praisonai-svc
```

### Typosquatting Protection
We maintain defensive packages for common typos:
- `praisonaisvc` → redirects to `praisonai-svc`
- `praisonai_svc` → redirects to `praisonai-svc`
- `praisonai-service` → redirects to `praisonai-svc`

### Report Security Issues
GitHub Issues: https://github.com/MervinPraison/PraisonAI-SVC/issues
```

**Maintenance:**

- **Cost:** Free (PyPI is free)
- **Effort:** One-time 30-minute setup
- **Updates:** Defensive packages auto-install latest main package
- **Monitoring:** Quarterly check for new typosquat attempts

**Alternative Considered:**

`praisonai-services` (plural) was considered as a more unique name with lower typosquat risk, but `praisonai-svc` was chosen for CLI consistency. Defensive registration mitigates the risk.

---

### 4.4 Handler Example (per-package repo)

```python
import io
from praisonai_svc import ServiceApp
from praisonaippt import build_ppt

app = ServiceApp("PraisonAI PPT")

@app.job
def generate_ppt(payload):
    buf = io.BytesIO()
    build_ppt(payload, out=buf)
    return (
        buf.getvalue(),
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "slides.pptx",
    )
```

---

### 4.5 API Endpoints

| Method | Path                  | Description                                                                     |
| ------ | --------------------- | ------------------------------------------------------------------------------- |
| `POST` | `/jobs`               | Accepts YAML/JSON (validated via Pydantic); enqueues job and returns `job_id`. |
| `GET`  | `/jobs/{id}`          | Returns `{status, download_url?}` from Table Storage.                           |
| `GET`  | `/jobs/{id}/download` | Generates fresh SAS URL on-demand (1h expiry); returns redirect or JSON link.   |
| `GET`  | `/health`             | Liveness check.                                                                 |

**Input Validation:**
- All payloads validated with strict Pydantic models
- Malformed YAML/JSON rejected with 400 error
- API key required via `X-API-Key` header (configurable)

---

### 4.6 Storage Schema

#### Table Storage: `jobs`

| PartitionKey | RowKey (job_id) | Status                             | DownloadURL | CreatedUTC | UpdatedUTC | StartedUTC | RetryCount | JobHash    | ErrorMsg |
| ------------ | --------------- | ---------------------------------- | ----------- | ---------- | ---------- | ---------- | ---------- | ---------- | -------- |
| `praison`    | `<uuid>`        | queued | processing | done | error | `<SAS URL>` | datetime   | datetime   | datetime   | int (0-3)  | SHA256     | string   |

**Field Notes:**
- **JobHash**: SHA256 of payload for idempotent retries (prevents duplicate processing)
- **RetryCount**: Tracks retry attempts (max 3 before moving to poison queue)
- **StartedUTC**: Worker processing start time (for timeout detection)
- **ErrorMsg**: Captured exception message for failed jobs

---

### 4.7 Azure Blob Upload + SAS Example

```python
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta

def upload_and_sign(data: bytes, filename: str):
    conn = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    client = BlobServiceClient.from_connection_string(conn)
    container = client.get_container_client("praison-output")
    blob = container.get_blob_client(filename)
    blob.upload_blob(data, overwrite=True)
    sas = generate_blob_sas(
        account_name=client.account_name,
        container_name="praison-output",
        blob_name=filename,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1),
    )
    return f"https://{client.account_name}.blob.core.windows.net/praison-output/{filename}?{sas}"
```

---

## 5. Azure Deployment Configuration

### 5.1 Container App Definition

```yaml
type: Microsoft.App/containerApps
properties:
  environmentId: <ACA_ENV_ID>
  configuration:
    ingress:
      external: true
      targetPort: 8080
      corsPolicy:
        allowedOrigins:
          - "https://your-wordpress-domain.com"
        allowedMethods:
          - GET
          - POST
          - OPTIONS
        allowedHeaders:
          - "*"
  template:
    containers:
      - name: api
        image: ghcr.io/praison/praisonai-ppt:latest
        resources:
          cpu: 1.0
          memory: 2Gi
        env:
          - name: AZURE_STORAGE_CONNECTION_STRING
            secretRef: storage-conn
          - name: AZURE_TABLE_CONN_STRING
            secretRef: table-conn
          - name: AZURE_QUEUE_CONN_STRING
            secretRef: queue-conn
      - name: worker
        image: ghcr.io/praison/praisonai-ppt:latest
        command: ["python", "-m", "praisonai_svc.worker"]
        resources:
          cpu: 1.0
          memory: 2Gi
        env:
          - name: AZURE_STORAGE_CONNECTION_STRING
            secretRef: storage-conn
          - name: AZURE_TABLE_CONN_STRING
            secretRef: table-conn
          - name: AZURE_QUEUE_CONN_STRING
            secretRef: queue-conn
    scale:
      minReplicas: 0
      maxReplicas: 3
      rules:
        - name: http
          http:
            concurrentRequests: 20
        - name: queue-depth
          azureQueue:
            queueName: praison-jobs
            queueLength: 10
            auth:
              - secretRef: queue-conn
                triggerParameter: connection
```

---

### 5.2 Cost Controls

| Resource                | Limit                   | Note                  |
| ----------------------- | ----------------------- | --------------------- |
| **ACA replicas**        | `maxReplicas: 3`        | hard cap              |
| **CPU/memory**          | `1 vCPU / 2 GiB`        | fixed                 |
| **Logging**             | daily limit < 500 MB    | avoid ingestion cost  |
| **Blob retention**      | 30 days lifecycle rule  | auto delete old files |
| **Storage Queue/Table** | pennies per million ops | negligible            |
| **Idle cost**           | zero (ACA scales to 0)  | pay only on use       |

---

## 6. WordPress Chatbot Integration

**Architecture:**

* JS chat widget on WordPress frontend (not PHP).
* Posts YAML/JSON to `https://<azure-app>.azurecontainerapps.io/jobs`.
* Polls `GET /jobs/{id}` every 5 s.
* When status = done, redirect browser → Blob SAS URL via `/jobs/{id}/download`.

**Benefits:**

* No PHP blocking.
* Works on shared hosting.
* Zero CPU load on WordPress.

**Security Implementation:**

1. **Option A: WordPress Proxy (Recommended)**
   ```php
   // WordPress REST endpoint
   add_action('rest_api_init', function() {
       register_rest_route('praisonai/v1', '/jobs', [
           'methods' => 'POST',
           'callback' => 'praisonai_proxy_job',
           'permission_callback' => 'is_user_logged_in'
       ]);
   });
   
   function praisonai_proxy_job($request) {
       $api_key = get_option('praisonai_api_key'); // Stored securely
       $response = wp_remote_post(AZURE_API_URL . '/jobs', [
           'headers' => ['X-API-Key' => $api_key],
           'body' => $request->get_json_params()
       ]);
       return json_decode(wp_remote_retrieve_body($response));
   }
   ```
   - API key never exposed to browser
   - WordPress handles authentication
   - CORS not required

2. **Option B: Direct API with CORS**
   - Configure ACA CORS to allow WordPress domain
   - Use JWT tokens issued by WordPress backend
   - Frontend includes JWT in requests
   - Azure validates JWT signature

**WP Plugin Features:**
- Shortcode: `[praisonai_chatbot service="ppt"]`
- Admin settings page for API configuration
- Job history dashboard
- Usage analytics

**Polling Strategy:**
```javascript
async function pollJobStatus(jobId) {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;
    
    while (attempts < maxAttempts) {
        const response = await fetch(`${API_URL}/jobs/${jobId}`);
        const job = await response.json();
        
        if (job.status === 'done') {
            window.location.href = `${API_URL}/jobs/${jobId}/download`;
            return;
        } else if (job.status === 'error') {
            showError(job.error_msg);
            return;
        }
        
        await sleep(5000); // 5 second interval
        attempts++;
    }
}
```

**Future: WebSocket Upgrade (v1.1)**
- Real-time progress updates
- Requires Redis PubSub or Azure SignalR Service
- Fallback to polling for compatibility

---

## 7. CLI (`praisonai-svc`)

| Command                                            | Function                                              |
| -------------------------------------------------- | ----------------------------------------------------- |
| `praisonai-svc new service <name> --package <pkg>` | Scaffold one-file handler project.                    |
| `praisonai-svc run`                                | Run FastAPI + worker locally.                         |
| `praisonai-svc deploy azure`                       | Build, push, and deploy to ACA with max replicas cap. |
| `praisonai-svc logs`                               | Tail logs from Azure Container App.                   |

---

## 8. Security and Access

| Area            | Implementation                                                      | Details                                                    |
| --------------- | ------------------------------------------------------------------- | ---------------------------------------------------------- |
| **Transport**   | HTTPS (ACA ingress)                                                 | TLS 1.2+ enforced                                          |
| **Auth**        | API Key via `X-API-Key` header                                      | FastAPI middleware validates against ACA Secret            |
| **Rate Limit**  | Table Storage-based counter                                         | 10 req/min per IP; 429 response when exceeded              |
| **CORS**        | Restricted to WordPress domain                                      | Prevents unauthorized cross-origin requests                |
| **Input Valid** | Pydantic models with strict schema                                  | Rejects malformed/oversized payloads (max 1MB)             |
| **Data**        | No DB persistence beyond Table Storage                              | Auto cleanup after 30 days via lifecycle policy            |
| **Files**       | SAS URLs with 1h expiry                                             | On-demand regeneration via `/jobs/{id}/download`           |
| **Secrets**     | ACA Secrets / Azure Key Vault                                       | Connection strings never in code                           |
| **WP Token**    | JWT issued by WP server (optional)                                  | Prevents exposing API key in browser; proxy token approach |

**Security Best Practices:**
- Never expose API keys in frontend JavaScript
- Use WordPress backend to proxy requests with server-side API key
- Implement request signing for high-security scenarios
- Monitor failed auth attempts via App Insights

---

## 9. Monitoring / Alerting

**Observability Stack:**
- Basic ACA log stream (stdout/stderr)
- App Insights with 10% sampling
- Daily log ingestion cap: 500 MB

**Alert Rules:**

| Metric                  | Threshold            | Action                              | Severity |
| ----------------------- | -------------------- | ----------------------------------- | -------- |
| CPU usage               | > 80% for 5 min      | Investigate job complexity          | Warning  |
| Memory usage            | > 90% for 3 min      | Check for memory leaks              | Critical |
| API error rate (5xx)    | > 2% in 5 min        | Trigger restart, check logs         | Critical |
| Job failure rate        | > 5% in 10 min       | Review error messages in Table      | Warning  |
| Queue length            | > 50 messages        | Auto-scale or notify (backlog)      | Info     |
| Queue length            | > 100 messages       | Alert on capacity issue             | Warning  |
| Failed auth attempts    | > 10 in 1 min        | Potential attack, log IP            | Warning  |
| Avg job duration        | > 5 min              | Performance degradation             | Info     |
| Blob upload failures    | > 3 in 5 min         | Check storage connectivity          | Critical |

**Metrics to Track:**
- Jobs processed per hour
- Average job processing time
- Queue wait time (queued → processing)
- SAS URL regeneration rate
- Retry/poison queue counts

---

## 10. Estimated Monthly Cost (UK Region, Small Load)

| Component             | Cost Estimate      | Notes                         |
| --------------------- | ------------------ | ----------------------------- |
| ACA (API + Worker)    | ~£10-£20           | scales to zero, 1 vCPU, 2 GiB |
| Blob Storage          | £1-£2              | ~10 GB data + egress          |
| Storage Queue + Table | < £1               | ~1 M ops                      |
| App Insights          | £1-£3              | with sampling and log cap     |
| **Total**             | **≈ £15-£25 / mo** | at modest traffic             |

---

## 11. Reliability & Error Handling

### 11.1 Worker Polling Efficiency

**Challenge:** Storage Queue polling wastes compute when queue is empty.

**Solution:**
```python
# Exponential backoff implementation
async def poll_queue_with_backoff():
    backoff = 1  # Start at 1 second
    max_backoff = 30  # Cap at 30 seconds
    
    while True:
        messages = await queue.receive_messages(max_messages=1, visibility_timeout=60)
        
        if messages:
            backoff = 1  # Reset on success
            await process_message(messages[0])
        else:
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)  # Exponential increase
```

**ACA Queue-Based Scaling:**
- Scale out when `messageCount > 10`
- Scale to 0 when `messageCount = 0`
- Result: **Zero polling cost at idle**

### 11.2 Failure Scenarios & Mitigations

| Failure Case              | Detection                              | Mitigation                                                  | Recovery Time |
| ------------------------- | -------------------------------------- | ----------------------------------------------------------- | ------------- |
| Worker crash mid-job      | Message visibility timeout expires     | Message reappears in queue; retry with incremented counter  | 60 seconds    |
| Blob upload failure       | Exception during upload                | 3 retries with exponential backoff (1s → 3s → 9s)           | < 15 seconds  |
| Job timeout               | `StartedUTC + 10 min < now()`          | Mark as failed, move to poison queue                        | 10 minutes    |
| Duplicate message         | JobHash match in Table Storage         | Idempotent: skip processing, return existing result         | Immediate     |
| Table Storage unavailable | Connection error                       | Retry 3x, then fail job with error message                  | < 30 seconds  |
| Malformed payload         | Pydantic validation error              | Reject at API level with 400 error (never queued)           | Immediate     |
| Queue unavailable         | Connection error on enqueue            | Return 503 to client, retry on client side                  | Immediate     |

### 11.3 Retry Logic

**Message Retry Flow:**
1. Worker receives message with `dequeue_count`
2. If `dequeue_count > 3`, move to **poison queue** (`praison-jobs-poison`)
3. Otherwise, process job and update `RetryCount` in Table Storage
4. On failure, message becomes visible again after 60s timeout

**Poison Queue Handling:**
- Manual review required for poison messages
- Admin endpoint: `GET /admin/poison-queue` (future)
- Alert when poison queue length > 5

### 11.4 Idempotency

**Job Hash Implementation:**
```python
import hashlib
import json

def compute_job_hash(payload: dict) -> str:
    """Generate deterministic hash for idempotent processing"""
    canonical = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()
```

**Usage:**
- Before processing, check if `JobHash` exists in Table Storage
- If exists and status = `done`, return existing result
- If exists and status = `processing`, check timeout
- Prevents duplicate work on retry

### 11.5 Timeout Management

**Job Timeout Detection:**
```python
from datetime import datetime, timedelta

MAX_JOB_DURATION = timedelta(minutes=10)

def check_timeout(job_entity):
    if job_entity.Status == "processing":
        started = job_entity.StartedUTC
        if datetime.utcnow() - started > MAX_JOB_DURATION:
            # Mark as failed
            job_entity.Status = "error"
            job_entity.ErrorMsg = "Job exceeded 10 minute timeout"
            table_client.update_entity(job_entity)
```

**Timeout Values:**
- API request timeout: 30 seconds
- Queue message visibility: 60 seconds
- Job processing timeout: 10 minutes
- Blob upload timeout: 2 minutes per file

### 11.6 Table Storage Limitations

| Limitation                | Impact                           | Mitigation                                                |
| ------------------------- | -------------------------------- | --------------------------------------------------------- |
| 1000 entities per query   | Job listing pagination needed    | Implement continuation tokens for admin endpoints         |
| No complex filtering      | Can't filter by user/type        | Client-side filtering for MVP; Cosmos DB upgrade later    |
| Eventual consistency      | 1-2s delay on status reads       | Acceptable for polling UI; client retries with delay      |
| 252 properties per entity | Schema size limit                | Current schema uses 9 fields (well within limit)          |
| 1MB entity size           | Large error messages truncated   | Truncate `ErrorMsg` to 10KB max                           |

### 11.7 Blob Storage Resilience

**Upload with Retry:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def upload_blob_with_retry(data: bytes, filename: str):
    blob_client = container_client.get_blob_client(filename)
    await blob_client.upload_blob(data, overwrite=True)
```

**SAS URL On-Demand Generation:**
```python
@app.get("/jobs/{job_id}/download")
async def download_job(job_id: str):
    job = await table_client.get_entity("praison", job_id)
    
    if job.Status != "done":
        raise HTTPException(404, "Job not ready")
    
    # Generate fresh SAS URL (1h expiry)
    sas_url = generate_blob_sas_url(job.BlobName)
    return RedirectResponse(sas_url)
```

**Benefits:**
- Users can download anytime (not limited to 1h window)
- Blobs remain private (no public access)
- Minimal overhead (SAS generation is fast)

---

## 12. Future Enhancements

| Version | Feature                 | Description                  |
| ------- | ----------------------- | ---------------------------- |
| v1.1    | WebSocket job updates   | Push progress to chatbot UI. |
| v1.2    | Multi-file outputs      | Batch ZIP download.          |
| v1.3    | Multi-tenant auth       | Per-organization API keys.   |
| v2.0    | Billing + usage metrics | SaaS tiering integration.    |

---

## 13. Implementation Roadmap

### Phase 1: MVP (v1.0) - Weeks 1-2

**Goal:** Basic working system with minimal features

| Component | Tasks | Deliverable |
|-----------|-------|-------------|
| **Core SDK** | - FastAPI app factory<br>- Queue push/poll helpers<br>- Table Storage CRUD<br>- Basic Blob upload | `praisonai-svc` package on PyPI |
| **Worker** | - Simple polling loop<br>- Job execution<br>- Status updates | Worker module in SDK |
| **API** | - `POST /jobs`<br>- `GET /jobs/{id}`<br>- `GET /health` | REST API endpoints |
| **CLI** | - `praisonai-svc new`<br>- `praisonai-svc run` | CLI tool |
| **Deployment** | - Dockerfile<br>- Basic ACA template | Deploy script |
| **Example** | - PraisonAIPPT handler | Working demo |
| **Security** | - PyPI 2FA setup<br>- Defensive package registration | 4 defensive packages |

**Success Criteria:**
- ✅ Can create PPT from YAML via API
- ✅ Job completes and returns download URL
- ✅ Runs locally and on Azure
- ✅ Cost < £25/month

### Phase 2: Resilience (v1.1) - Week 3

**Goal:** Production-ready reliability

| Feature | Implementation | Priority |
|---------|----------------|----------|
| **Retry Logic** | - Poison queue<br>- Retry counter<br>- Exponential backoff | Critical |
| **Idempotency** | - JobHash implementation<br>- Duplicate detection | Critical |
| **Timeout** | - Job timeout detection<br>- Cleanup of stale jobs | High |
| **Error Handling** | - Blob upload retry<br>- Table Storage retry<br>- Error messages | High |
| **Monitoring** | - App Insights alerts<br>- Metrics dashboard | Medium |

**Success Criteria:**
- ✅ Worker crashes don't lose jobs
- ✅ Retries work correctly
- ✅ Timeouts are detected and handled
- ✅ Alerts fire on failures

### Phase 3: Security (v1.2) - Week 4

**Goal:** Production-grade security

| Feature | Implementation | Priority |
|---------|----------------|----------|
| **Auth** | - API key middleware<br>- Key rotation support | Critical |
| **Rate Limiting** | - Table Storage counter<br>- IP-based limits | High |
| **Input Validation** | - Pydantic models<br>- Size limits (1MB) | Critical |
| **CORS** | - Domain whitelist<br>- Preflight handling | High |
| **Secrets** | - Key Vault integration<br>- No hardcoded secrets | Critical |

**Success Criteria:**
- ✅ API key required for all requests
- ✅ Rate limiting prevents abuse
- ✅ Invalid input rejected
- ✅ CORS configured correctly

### Phase 4: UX Improvements (v1.3) - Week 5

**Goal:** Better user experience

| Feature | Implementation | Priority |
|---------|----------------|----------|
| **Download Endpoint** | - `/jobs/{id}/download`<br>- On-demand SAS generation | High |
| **WordPress Plugin** | - PHP proxy endpoint<br>- Admin settings page<br>- Shortcode support | Medium |
| **Job Listing** | - `GET /jobs` with pagination<br>- Filter by status | Low |
| **Progress Updates** | - WebSocket support (optional)<br>- Progress percentage | Low |

**Success Criteria:**
- ✅ Users can download anytime (not limited to 1h)
- ✅ WordPress plugin installable
- ✅ Admin can view job history

### Phase 5: Scale & Optimize (v1.4) - Week 6+

**Goal:** Performance and cost optimization

| Feature | Implementation | Priority |
|---------|----------------|----------|
| **Queue Scaling** | - Queue-depth based autoscale<br>- Worker efficiency metrics | Medium |
| **Caching** | - Job result caching<br>- Duplicate job detection | Low |
| **Analytics** | - Usage dashboard<br>- Cost tracking<br>- Performance metrics | Low |
| **Multi-Service** | - Deploy PraisonAIVideo<br>- Deploy PraisonAIWP<br>- Shared infrastructure | Medium |

**Success Criteria:**
- ✅ Workers scale efficiently
- ✅ Cost remains < £25/month
- ✅ Multiple services deployed
- ✅ Analytics dashboard available

### Development Priorities

**Must Have (MVP):**
1. Basic API + Worker
2. Queue + Table + Blob integration
3. Local development support
4. Azure deployment

**Should Have (v1.1-1.2):**
1. Retry logic + poison queue
2. API key authentication
3. Error handling + monitoring
4. Download endpoint

**Nice to Have (v1.3+):**
1. WordPress plugin
2. WebSocket updates
3. Job listing/history
4. Analytics dashboard

---

## ✅ Final Deliverables

1. **SDK (`praisonai-svc`)**

   * FastAPI + Queue + Storage + CLI.
   * Published on PyPI with 2FA enabled.
2. **Defensive Packages**

   * `praisonaisvc`, `praisonai_svc`, `praisonai-service`, `praisonai-svcs`
   * Auto-redirect to main package.
   * Typosquatting protection.
3. **Minimal Azure Infra Template**

   * Single ACA (two containers) + Blob + Storage Queue + Table.
4. **Example Service**

   * `praisonai-ppt` repo with `handlers.py`.
5. **WordPress Integration Snippet**

   * JS chat widget calling API directly.
6. **Cost and Scaling Config**

   * Hard-capped replicas, scale-to-zero, retention policies.

---

### 🔚 **Outcome**

**Core Achievements:**
* ✅ One-file service pattern → new AI tools online in minutes
* ✅ Fully Azure native → no VM management, serverless architecture
* ✅ Costs capped at £15-25/month with scale-to-zero
* ✅ Production-ready reliability with retry logic and error handling
* ✅ Secure by default with API keys, rate limiting, and CORS
* ✅ WordPress-native integration → fast UX, zero backend load

**Technical Wins:**
* Queue-depth based autoscaling (0 cost at idle)
* Idempotent job processing (retry-safe)
* On-demand SAS URL generation (no expiry issues)
* Exponential backoff polling (efficient worker utilization)
* Poison queue for failed jobs (no data loss)
* Comprehensive monitoring and alerting

**Business Value:**
* Predictable, minimal costs (no surprise bills)
* Rapid service deployment (hours, not days)
* Scalable foundation for all PraisonAI micro-services
* WordPress ecosystem integration (millions of potential users)
* Production-grade from day one (retry, timeout, monitoring)

**Next Steps:**
1. Implement MVP (Phase 1) - 2 weeks
2. Add resilience (Phase 2) - 1 week
3. Harden security (Phase 3) - 1 week
4. Deploy first service (PraisonAIPPT)
5. Expand to additional services (Video, WP, etc.)
