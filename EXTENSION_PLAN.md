# PraisonAI Service Framework - Extension Plan
## Supporting Text Responses, Mixed Responses, and Streaming Status Updates

**Date:** November 5, 2025  
**Current Version:** 1.2.0  
**Target Version:** 2.0.0  
**Status:** 📋 Planning Phase

---

## Executive Summary

This document outlines a comprehensive plan to extend the PraisonAI Service Framework to support:

1. **Text-only responses** (no file generation)
2. **Mixed responses** (text + file)
3. **Streaming status updates** (real-time progress notifications)

**Core Principle:** Maintain the one-file simplicity while adding powerful new capabilities through backward-compatible extensions.

---

## Table of Contents

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [Requirements & Use Cases](#requirements--use-cases)
3. [Research Findings](#research-findings)
4. [Proposed Solutions](#proposed-solutions)
5. [Implementation Plan](#implementation-plan)
6. [Migration Strategy](#migration-strategy)
7. [Testing Strategy](#testing-strategy)

---

## Current Architecture Analysis

### Current Flow

```
Client → POST /jobs → Queue → Worker → Blob Storage → Table Storage → Client polls GET /jobs/{id}
```

### Current Limitations

1. **File-only results**: Handler must return `tuple[bytes, str, str]` (file_data, content_type, filename)
2. **No text responses**: Cannot return simple text/JSON without creating a file
3. **No streaming**: Client must poll for status, no real-time updates
4. **No progress tracking**: No way to report intermediate progress (e.g., "Step 1 of 5 complete")

### Current Strengths (Must Preserve)

✅ **One-file simplicity**: `app.py` is all you need  
✅ **Idempotency**: Hash-based duplicate detection  
✅ **Retry logic**: Exponential backoff, poison queue  
✅ **Azure-native**: Blob, Queue, Table Storage  
✅ **Scale-to-zero**: Cost-effective  
✅ **Type safety**: Pydantic models  

---

## Requirements & Use Cases

### Use Case 1: Text-Only Response

**Example:** Chatbot, text analysis, simple computation

```python
@app.job
def analyze_sentiment(payload: dict) -> dict:
    text = payload['text']
    return {
        'sentiment': 'positive',
        'score': 0.95,
        'summary': 'Very positive sentiment detected'
    }
```

**Client Experience:**
```bash
# Create job
curl -X POST /jobs -d '{"payload": {"text": "I love this!"}}'
# Response: {"job_id": "abc123", "status": "queued"}

# Poll for result
curl /jobs/abc123
# Response: {
#   "job_id": "abc123",
#   "status": "done",
#   "result": {
#     "sentiment": "positive",
#     "score": 0.95,
#     "summary": "Very positive sentiment detected"
#   }
# }
```

### Use Case 2: Mixed Response (Text + File)

**Example:** Report generation with summary

```python
@app.job
def generate_report(payload: dict) -> dict:
    pdf_data = create_pdf_report(payload)
    return {
        'summary': 'Report generated with 42 pages',
        'page_count': 42,
        'file': {
            'data': pdf_data,
            'content_type': 'application/pdf',
            'filename': 'report.pdf'
        }
    }
```

**Client Experience:**
```bash
curl /jobs/abc123
# Response: {
#   "job_id": "abc123",
#   "status": "done",
#   "result": {
#     "summary": "Report generated with 42 pages",
#     "page_count": 42
#   },
#   "download_url": "https://blob.../report.pdf?sas=..."
# }
```

### Use Case 3: Streaming Status Updates

**Example:** Multi-step processing with progress

```python
@app.job
async def process_video(payload: dict, progress):
    await progress.update('Downloading video...', step=1, total=5)
    video = download_video(payload['url'])
    
    await progress.update('Extracting audio...', step=2, total=5)
    audio = extract_audio(video)
    
    await progress.update('Transcribing...', step=3, total=5)
    transcript = transcribe(audio)
    
    await progress.update('Analyzing...', step=4, total=5)
    analysis = analyze(transcript)
    
    await progress.update('Generating report...', step=5, total=5)
    return {'transcript': transcript, 'analysis': analysis}
```

**Client Experience (SSE):**
```javascript
const eventSource = new EventSource('/jobs/abc123/stream');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
  // { status: 'processing', message: 'Downloading video...', progress: 20 }
  // { status: 'processing', message: 'Extracting audio...', progress: 40 }
  // { status: 'done', result: {...} }
};
```

---

## Research Findings

### 1. Response Type Patterns

**Industry Standard: Polymorphic Responses**

Modern APIs use discriminated unions:

```typescript
type JobResult = 
  | { type: 'text', data: any }
  | { type: 'file', url: string, metadata: any }
  | { type: 'mixed', data: any, files: FileInfo[] }
```

**Advantages:**
- ✅ Type-safe
- ✅ Extensible
- ✅ Clear intent
- ✅ Easy to parse

### 2. Streaming Patterns

**Option A: Server-Sent Events (SSE)**
- ✅ Simple HTTP-based
- ✅ Auto-reconnect
- ✅ UTF-8 only (sufficient for status)
- ✅ One-way (server → client)
- ✅ Works through firewalls
- ⚠️ No binary data

**Option B: WebSockets**
- ✅ Full-duplex
- ✅ Binary support
- ⚠️ More complex
- ⚠️ Requires WebSocket infrastructure
- ⚠️ Firewall issues

**Recommendation: SSE** for status updates (simpler, sufficient)

### 3. Azure Storage Patterns

**Schema Evolution in Table Storage:**
- ✅ Azure Table Storage is schema-less
- ✅ Can add new properties without breaking existing code
- ✅ Backward compatible by design

**Example:**
```python
# Old entity
JobEntity(RowKey='123', Status='done', DownloadURL='...')

# New entity (backward compatible)
JobEntity(
    RowKey='456', 
    Status='done', 
    ResultType='text',  # NEW
    ResultData='...',   # NEW
    DownloadURL=None    # Optional now
)
```

---

## Proposed Solutions

### Solution 1: Polymorphic Handler Return Types (Recommended)

**Extend handler signature to support multiple return types:**

```python
from typing import Union
from praisonai_svc import ServiceApp, TextResult, FileResult, MixedResult

app = ServiceApp("My Service")

# Option 1: Text-only
@app.job
def text_handler(payload: dict) -> TextResult:
    return TextResult(data={'message': 'Hello'})

# Option 2: File-only (backward compatible)
@app.job
def file_handler(payload: dict) -> FileResult:
    return FileResult(
        data=b'...',
        content_type='application/pdf',
        filename='report.pdf'
    )

# Option 3: Mixed
@app.job
def mixed_handler(payload: dict) -> MixedResult:
    return MixedResult(
        data={'summary': 'Report ready'},
        files=[
            FileResult(data=b'...', content_type='application/pdf', filename='report.pdf')
        ]
    )

# Option 4: Legacy (still supported)
@app.job
def legacy_handler(payload: dict) -> tuple[bytes, str, str]:
    return (b'...', 'text/plain', 'result.txt')
```

**Implementation:**

```python
# New models in models/result.py
from pydantic import BaseModel
from typing import Any, List

class TextResult(BaseModel):
    """Text-only result."""
    type: str = 'text'
    data: Any

class FileResult(BaseModel):
    """File result."""
    type: str = 'file'
    data: bytes
    content_type: str
    filename: str

class MixedResult(BaseModel):
    """Mixed text + files result."""
    type: str = 'mixed'
    data: Any
    files: List[FileResult]

# Union type for handler return
JobResult = Union[TextResult, FileResult, MixedResult, tuple[bytes, str, str]]
```

**Worker changes:**

```python
# worker.py - handle different result types
result = self.job_handler(payload)

if isinstance(result, tuple):
    # Legacy: (bytes, str, str)
    file_data, content_type, filename = result
    blob_name = f"{job_id}/{filename}"
    await self.blob_storage.upload_blob(file_data, blob_name)
    download_url = self.blob_storage.generate_sas_url(blob_name)
    await self.table_storage.update_job(
        job_id,
        status=JobStatus.DONE,
        result_type='file',
        download_url=download_url,
        blob_name=blob_name
    )

elif isinstance(result, TextResult):
    # Text-only result
    await self.table_storage.update_job(
        job_id,
        status=JobStatus.DONE,
        result_type='text',
        result_data=json.dumps(result.data)
    )

elif isinstance(result, FileResult):
    # File result (new style)
    blob_name = f"{job_id}/{result.filename}"
    await self.blob_storage.upload_blob(result.data, blob_name)
    download_url = self.blob_storage.generate_sas_url(blob_name)
    await self.table_storage.update_job(
        job_id,
        status=JobStatus.DONE,
        result_type='file',
        download_url=download_url,
        blob_name=blob_name
    )

elif isinstance(result, MixedResult):
    # Mixed result
    file_urls = []
    for file in result.files:
        blob_name = f"{job_id}/{file.filename}"
        await self.blob_storage.upload_blob(file.data, blob_name)
        url = self.blob_storage.generate_sas_url(blob_name)
        file_urls.append({'filename': file.filename, 'url': url})
    
    await self.table_storage.update_job(
        job_id,
        status=JobStatus.DONE,
        result_type='mixed',
        result_data=json.dumps(result.data),
        file_urls=json.dumps(file_urls)
    )
```

**Table Storage schema (backward compatible):**

```python
class JobEntity(BaseModel):
    PartitionKey: str = "praison"
    RowKey: str  # job_id
    Status: str
    
    # Existing fields (kept for backward compatibility)
    DownloadURL: str | None = None
    BlobName: str | None = None
    
    # NEW fields (optional, backward compatible)
    ResultType: str | None = None  # 'text', 'file', 'mixed'
    ResultData: str | None = None  # JSON string for text/mixed results
    FileURLs: str | None = None    # JSON array for mixed results
    
    # Existing metadata
    CreatedUTC: datetime
    UpdatedUTC: datetime
    StartedUTC: datetime | None = None
    RetryCount: int = 0
    JobHash: str
    ErrorMsg: str | None = None
```

**API Response (backward compatible):**

```python
class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    
    # Existing fields (kept)
    download_url: str | None = None
    
    # NEW fields (optional)
    result_type: str | None = None
    result: Any | None = None  # For text/mixed results
    files: List[dict] | None = None  # For mixed results
    
    # Metadata
    error_msg: str | None = None
    created_utc: datetime
    updated_utc: datetime
    started_utc: datetime | None = None
    retry_count: int = 0
```

**Backward Compatibility:**
- ✅ Old handlers still work (tuple return)
- ✅ Old clients still work (download_url present for file results)
- ✅ New clients can check `result_type` to handle different responses
- ✅ Table Storage schema is additive (no breaking changes)

---

### Solution 2: Streaming Status Updates via SSE

**Add streaming endpoint:**

```python
# app.py - new endpoint
@self.app.get("/jobs/{job_id}/stream")
async def stream_job_status(job_id: str):
    """Stream job status updates via SSE."""
    async def event_generator():
        last_status = None
        while True:
            job = await self.table_storage.get_job(job_id)
            if not job:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Job not found"})
                }
                break
            
            # Send update if status changed or progress updated
            current_status = {
                'status': job.Status,
                'message': job.ProgressMessage,
                'progress': job.ProgressPercent,
                'step': job.ProgressStep,
                'total_steps': job.TotalSteps
            }
            
            if current_status != last_status:
                yield {
                    "event": "status",
                    "data": json.dumps(current_status)
                }
                last_status = current_status
            
            # Stop streaming when done or failed
            if job.Status in [JobStatus.DONE.value, JobStatus.ERROR.value]:
                if job.Status == JobStatus.DONE.value:
                    # Send final result
                    response = job.to_response()
                    yield {
                        "event": "complete",
                        "data": json.dumps(response.dict())
                    }
                break
            
            await asyncio.sleep(1)  # Poll every second
    
    return EventSourceResponse(event_generator())
```

**Progress tracking in worker:**

```python
# worker.py - add progress context
class ProgressTracker:
    """Context for tracking job progress."""
    
    def __init__(self, job_id: str, table_storage: TableStorage):
        self.job_id = job_id
        self.table_storage = table_storage
    
    async def update(
        self, 
        message: str, 
        step: int | None = None, 
        total: int | None = None,
        percent: int | None = None
    ):
        """Update job progress."""
        await self.table_storage.update_job_progress(
            self.job_id,
            message=message,
            step=step,
            total_steps=total,
            percent=percent
        )

# In worker process
progress = ProgressTracker(job_id, self.table_storage)

# Check if handler accepts progress parameter
import inspect
sig = inspect.signature(self.job_handler)
if 'progress' in sig.parameters:
    # New-style handler with progress
    result = await self.job_handler(payload, progress=progress)
else:
    # Legacy handler without progress
    result = self.job_handler(payload)
```

**Handler with progress:**

```python
@app.job
async def process_video(payload: dict, progress) -> TextResult:
    await progress.update('Downloading...', step=1, total=5, percent=20)
    video = download_video(payload['url'])
    
    await progress.update('Processing...', step=2, total=5, percent=40)
    result = process(video)
    
    await progress.update('Finalizing...', step=5, total=5, percent=100)
    return TextResult(data={'result': result})
```

**Table Storage schema additions:**

```python
class JobEntity(BaseModel):
    # ... existing fields ...
    
    # NEW: Progress tracking
    ProgressMessage: str | None = None
    ProgressPercent: int | None = None
    ProgressStep: int | None = None
    TotalSteps: int | None = None
```

**Client usage:**

```javascript
// JavaScript client
const eventSource = new EventSource(`/jobs/${jobId}/stream`);

eventSource.addEventListener('status', (e) => {
    const data = JSON.parse(e.data);
    console.log(`${data.message} (${data.progress}%)`);
    updateProgressBar(data.progress);
});

eventSource.addEventListener('complete', (e) => {
    const data = JSON.parse(e.data);
    console.log('Job complete!', data.result);
    eventSource.close();
});

eventSource.addEventListener('error', (e) => {
    console.error('Error:', e);
    eventSource.close();
});
```

```python
# Python client
import sseclient
import requests

response = requests.get(f'/jobs/{job_id}/stream', stream=True)
client = sseclient.SSEClient(response)

for event in client.events():
    if event.event == 'status':
        data = json.loads(event.data)
        print(f"{data['message']} ({data['progress']}%)")
    elif event.event == 'complete':
        data = json.loads(event.data)
        print('Complete!', data['result'])
        break
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Goal:** Add polymorphic result types without breaking existing code

1. **Create new result models** (`models/result.py`)
   - `TextResult`
   - `FileResult`
   - `MixedResult`
   - `JobResult` union type

2. **Extend Table Storage schema** (`azure/table.py`)
   - Add `ResultType`, `ResultData`, `FileURLs` fields
   - Maintain backward compatibility

3. **Update worker** (`worker.py`)
   - Add result type detection
   - Handle each result type appropriately
   - Keep legacy tuple support

4. **Update API responses** (`models/job.py`)
   - Add `result_type`, `result`, `files` to `JobResponse`
   - Keep `download_url` for backward compatibility

5. **Write tests**
   - Test each result type
   - Test backward compatibility
   - Test mixed scenarios

### Phase 2: Streaming (Week 2)

**Goal:** Add SSE streaming for real-time status updates

1. **Add SSE endpoint** (`app.py`)
   - `GET /jobs/{id}/stream`
   - EventSourceResponse implementation

2. **Add progress tracking** (`worker.py`)
   - `ProgressTracker` class
   - Automatic handler inspection
   - Table Storage progress updates

3. **Extend Table Storage** (`azure/table.py`)
   - Add progress fields
   - Add `update_job_progress` method

4. **Add SSE dependency**
   - `sse-starlette` to `pyproject.toml`

5. **Write tests**
   - Test SSE streaming
   - Test progress updates
   - Test client reconnection

### Phase 3: Documentation & Examples (Week 3)

**Goal:** Make it easy for users to adopt new features

1. **Update README**
   - Add examples for each result type
   - Add SSE streaming example
   - Update quick start

2. **Create examples**
   - `examples/text-service/` - Text-only chatbot
   - `examples/mixed-service/` - Report with summary
   - `examples/streaming-service/` - Video processing with progress

3. **Update CLI templates**
   - Add `--type` flag to `praisonai-svc new`
   - Generate appropriate template based on type

4. **Migration guide**
   - How to upgrade existing services
   - Backward compatibility guarantees

### Phase 4: Testing & Release (Week 4)

**Goal:** Ensure production readiness

1. **Integration testing**
   - End-to-end tests for all result types
   - SSE streaming tests
   - Load testing with k6

2. **Performance testing**
   - Benchmark different result types
   - SSE connection limits
   - Memory usage

3. **Documentation review**
   - API reference
   - Architecture diagrams
   - Troubleshooting guide

4. **Release**
   - Version 2.0.0
   - PyPI publication
   - Announcement

---

## Migration Strategy

### For Existing Users

**No breaking changes:**

```python
# Old code (still works)
@app.job
def process(payload: dict) -> tuple[bytes, str, str]:
    return (b'data', 'text/plain', 'file.txt')
```

**Opt-in to new features:**

```python
# New code (opt-in)
from praisonai_svc import TextResult

@app.job
def process(payload: dict) -> TextResult:
    return TextResult(data={'message': 'Hello'})
```

### Deprecation Timeline

- **v2.0.0**: New features added, legacy fully supported
- **v2.x.x**: Both styles supported indefinitely
- **v3.0.0** (future): Consider deprecation warnings for tuple returns
- **v4.0.0** (distant future): Potentially remove tuple support

**Recommendation:** Support both styles indefinitely (no forced migration)

---

## Testing Strategy

### Unit Tests

```python
# tests/test_result_types.py
def test_text_result():
    result = TextResult(data={'message': 'Hello'})
    assert result.type == 'text'
    assert result.data['message'] == 'Hello'

def test_file_result():
    result = FileResult(
        data=b'content',
        content_type='text/plain',
        filename='test.txt'
    )
    assert result.type == 'file'

def test_mixed_result():
    result = MixedResult(
        data={'summary': 'Done'},
        files=[FileResult(...)]
    )
    assert result.type == 'mixed'
    assert len(result.files) == 1

def test_legacy_tuple():
    # Ensure tuple returns still work
    result = (b'data', 'text/plain', 'file.txt')
    assert isinstance(result, tuple)
```

### Integration Tests

```python
# tests/test_integration_results.py
async def test_text_result_end_to_end():
    # Create job
    response = await client.post('/jobs', json={'payload': {...}})
    job_id = response.json()['job_id']
    
    # Wait for completion
    await wait_for_job(job_id)
    
    # Check result
    response = await client.get(f'/jobs/{job_id}')
    data = response.json()
    assert data['result_type'] == 'text'
    assert data['result'] is not None
    assert data['download_url'] is None

async def test_sse_streaming():
    # Create job
    job_id = await create_job()
    
    # Stream status
    events = []
    async with client.stream('GET', f'/jobs/{job_id}/stream') as response:
        async for line in response.aiter_lines():
            if line.startswith('data:'):
                events.append(json.loads(line[5:]))
    
    # Verify events
    assert len(events) > 0
    assert events[-1]['status'] == 'done'
```

### Load Tests

```javascript
// k6-result-types.js
export default function() {
    // Test text results
    let res = http.post(`${BASE_URL}/jobs`, JSON.stringify({
        payload: {type: 'text', ...}
    }));
    check(res, {'text job created': (r) => r.status === 200});
    
    // Test file results
    res = http.post(`${BASE_URL}/jobs`, JSON.stringify({
        payload: {type: 'file', ...}
    }));
    check(res, {'file job created': (r) => r.status === 200});
    
    // Test SSE streaming
    let sse = http.get(`${BASE_URL}/jobs/${jobId}/stream`);
    check(sse, {'sse connected': (r) => r.status === 200});
}
```

---

## Alternative Approaches Considered

### Alternative 1: Separate Endpoints

**Approach:** Different endpoints for different result types

```python
POST /jobs/text
POST /jobs/file
POST /jobs/mixed
```

**Rejected because:**
- ❌ More complex API surface
- ❌ Harder to maintain
- ❌ Breaks one-file simplicity
- ❌ Client needs to know type upfront

### Alternative 2: WebSockets Instead of SSE

**Approach:** Use WebSockets for streaming

**Rejected because:**
- ❌ More complex (full-duplex not needed)
- ❌ Harder to implement
- ❌ Firewall issues
- ❌ No auto-reconnect
- ✅ SSE is simpler and sufficient

### Alternative 3: Polling-Only (No Streaming)

**Approach:** Keep current polling, add progress fields

**Rejected because:**
- ❌ Poor UX for long-running jobs
- ❌ Increased server load (constant polling)
- ❌ Higher latency
- ✅ SSE provides better experience

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes | HIGH | Maintain backward compatibility, extensive testing |
| Performance degradation | MEDIUM | Benchmark all changes, optimize hot paths |
| SSE connection limits | MEDIUM | Document limits, add connection pooling |
| Table Storage schema issues | LOW | Azure Table is schema-less, additive changes only |

### User Experience Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Confusion about result types | MEDIUM | Clear documentation, good examples |
| Migration complexity | LOW | No forced migration, both styles supported |
| Learning curve | LOW | Opt-in features, legacy still works |

---

## Success Metrics

### Technical Metrics

- ✅ 100% backward compatibility (all existing tests pass)
- ✅ <5% performance overhead for new features
- ✅ <100ms latency for SSE updates
- ✅ Support 1000+ concurrent SSE connections

### User Metrics

- ✅ 3+ example services demonstrating new features
- ✅ <10 lines of code to add streaming
- ✅ <5 lines to switch to text results
- ✅ Zero breaking changes for existing users

---

## Open Questions

1. **Should we support binary data in SSE?**
   - Current: UTF-8 only (sufficient for status)
   - Alternative: Base64 encode binary (adds overhead)
   - **Recommendation:** UTF-8 only, use polling for binary

2. **Should progress be mandatory or optional?**
   - Current: Optional (handler inspection)
   - Alternative: Always pass progress parameter
   - **Recommendation:** Optional (backward compatible)

3. **Should we add WebSocket support later?**
   - Current: SSE only
   - Future: Add WebSocket for bidirectional needs
   - **Recommendation:** Start with SSE, add WS in v2.1 if needed

4. **Should we version the API?**
   - Current: Single API, backward compatible
   - Alternative: `/v2/jobs` for new features
   - **Recommendation:** Single API, use `result_type` field

---

## Conclusion

This plan provides a **clear, backward-compatible path** to extend the PraisonAI Service Framework with:

1. **Polymorphic result types** (text, file, mixed)
2. **SSE streaming** for real-time status updates
3. **Progress tracking** for long-running jobs

**Key Principles:**
- ✅ Maintain one-file simplicity
- ✅ Zero breaking changes
- ✅ Opt-in features
- ✅ Clear migration path
- ✅ Comprehensive testing

**Next Steps:**
1. Review and approve this plan
2. Create detailed technical specs for Phase 1
3. Begin implementation
4. Iterate based on feedback

---

**Document Version:** 1.0  
**Last Updated:** November 5, 2025  
**Author:** PraisonAI Team  
**Status:** Ready for Review
