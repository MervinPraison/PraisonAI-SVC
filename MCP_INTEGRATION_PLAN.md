# PraisonAI Service Framework - MCP Integration Plan
## Making Your Application MCP-Compatible by Design

**Date:** November 5, 2025  
**Current Version:** 1.2.0  
**Target Version:** 2.0.0 (MCP-Compatible)  
**Status:** 📋 Planning Phase

---

## Executive Summary

This document outlines a comprehensive plan to make the PraisonAI Service Framework **MCP-compatible by design**, transforming it from a pure REST API service into a **Model Context Protocol (MCP) server** that can be natively integrated with AI applications like Claude, ChatGPT, and other LLM-powered tools.

**Core Principle:** Maintain one-file simplicity while adding MCP capabilities that make your services AI-native and discoverable.

**What is MCP?** Think of MCP as "USB-C for AI" - a standardized protocol that lets AI applications connect to your services, data, and tools seamlessly.

---

## Table of Contents

1. [What is MCP?](#what-is-mcp)
2. [Why MCP for PraisonAI-SVC?](#why-mcp-for-praisonai-svc)
3. [MCP Core Concepts](#mcp-core-concepts)
4. [Implementation Approaches](#implementation-approaches)
5. [Recommended Architecture](#recommended-architecture)
6. [Implementation Plan](#implementation-plan)
7. [Migration Strategy](#migration-strategy)
8. [Benefits & Use Cases](#benefits--use-cases)

---

## What is MCP?

### Overview

**Model Context Protocol (MCP)** is an open standard introduced by Anthropic in November 2024 for connecting AI applications to external systems. It provides a standardized way for LLMs to:

- **Access data** (Resources)
- **Execute actions** (Tools)
- **Use templates** (Prompts)

### The Three Pillars of MCP

| Feature | Control | Purpose | Example |
|---------|---------|---------|---------|
| **Tools** | Model-controlled | Actions the LLM can invoke | Create job, check status, download file |
| **Resources** | App-controlled | Read-only data for context | Job history, system logs, documentation |
| **Prompts** | User-controlled | Reusable templates | "Generate report", "Analyze results" |

### MCP vs REST API

```
Traditional REST API:
Client → HTTP Request → Server → HTTP Response → Client

MCP:
AI Agent → MCP Protocol → Server → Structured Response → AI Agent
         ↓
    (Discovers tools, resources, prompts automatically)
```

**Key Difference:** MCP is **self-describing** - AI agents can discover what your service does without documentation.

---

## Why MCP for PraisonAI-SVC?

### Current State

Your framework currently provides:
- ✅ REST API endpoints (`POST /jobs`, `GET /jobs/{id}`)
- ✅ Job queue system
- ✅ File generation and storage
- ✅ Status polling

### With MCP Integration

Your framework will provide:
- ✅ **AI-native integration** - Claude/ChatGPT can use your service directly
- ✅ **Auto-discovery** - AI agents discover capabilities automatically
- ✅ **Structured interactions** - Type-safe tool calls
- ✅ **Context-aware** - Provide job history, logs as resources
- ✅ **Template-driven** - Reusable prompts for common workflows
- ✅ **Backward compatible** - REST API still works

### Real-World Benefits

**Before MCP:**
```python
# User manually calls API
response = requests.post('/jobs', json={'payload': {...}})
job_id = response.json()['job_id']
# Wait and poll...
result = requests.get(f'/jobs/{job_id}')
```

**With MCP:**
```
User: "Generate a PowerPoint about AI trends"
Claude: [Discovers create_presentation tool]
Claude: [Calls tool with structured params]
Claude: [Monitors progress via resources]
Claude: "I've created your presentation. Here's the download link..."
```

---

## MCP Core Concepts

### 1. Tools (Actions)

Tools are functions AI can invoke. In PraisonAI-SVC context:

```python
@mcp.tool()
def create_job(payload: dict) -> dict:
    """Create a new processing job.
    
    Args:
        payload: Job configuration and data
        
    Returns:
        Job ID and status
    """
    # Your existing logic
    job_id = create_job_internal(payload)
    return {"job_id": job_id, "status": "queued"}

@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """Check job processing status.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Current job status and details
    """
    return get_job_from_table(job_id)
```

**AI Agent discovers:**
- Tool name: `create_job`
- Parameters: `payload` (dict)
- Return type: `dict` with job_id and status
- Description from docstring

### 2. Resources (Data)

Resources provide read-only context. Examples for PraisonAI-SVC:

```python
@mcp.resource("jobs://recent")
def get_recent_jobs() -> str:
    """Returns list of recent jobs"""
    jobs = table_storage.list_recent_jobs(limit=10)
    return json.dumps(jobs)

@mcp.resource("jobs://{job_id}/logs")
def get_job_logs(job_id: str) -> str:
    """Returns processing logs for a job"""
    logs = get_logs_for_job(job_id)
    return logs

@mcp.resource("system://stats")
def get_system_stats() -> str:
    """Returns system statistics"""
    return json.dumps({
        "total_jobs": count_jobs(),
        "active_workers": count_workers(),
        "queue_size": get_queue_size()
    })
```

**AI Agent can:**
- Browse recent jobs for context
- Read logs to troubleshoot
- Check system health

### 3. Prompts (Templates)

Prompts are reusable templates:

```python
@mcp.prompt()
def analyze_job_results(job_id: str) -> str:
    """Generate analysis prompt for job results"""
    job = get_job(job_id)
    return f"""Analyze the following job results:
    
Job ID: {job_id}
Status: {job.status}
Created: {job.created_utc}
Result: {job.result}

Provide insights on:
1. Success/failure reasons
2. Performance metrics
3. Recommendations
"""
```

---

## Implementation Approaches

### Approach 1: FastMCP Integration (Recommended)

**What:** Use FastMCP library to add MCP capabilities alongside FastAPI

**Pros:**
- ✅ Minimal code changes
- ✅ Maintains existing REST API
- ✅ One-file simplicity preserved
- ✅ Built-in OAuth support
- ✅ Production-ready

**Cons:**
- ⚠️ Additional dependency

**Implementation:**

```python
from praisonai_svc import ServiceApp
from fastmcp import FastMCP

# Existing code
app = ServiceApp("My Service")

# Add MCP layer
mcp = FastMCP("My Service MCP")

@app.job
def process_job(payload: dict) -> tuple[bytes, str, str]:
    # Existing handler
    return (data, content_type, filename)

# Expose as MCP tool
@mcp.tool()
async def create_job(payload: dict) -> dict:
    """Create processing job"""
    # Reuse existing logic
    job_id = await app.create_job_internal(payload)
    return {"job_id": job_id}

# Run both
if __name__ == "__main__":
    # Start FastAPI + MCP
    app.run_with_mcp(mcp)
```

### Approach 2: FastAPI-MCP (Auto-exposure)

**What:** Automatically expose FastAPI endpoints as MCP tools

**Pros:**
- ✅ Zero code changes to endpoints
- ✅ Automatic tool generation
- ✅ Works with existing API

**Cons:**
- ⚠️ Less control over MCP schema
- ⚠️ May expose unwanted endpoints

**Implementation:**

```python
from fastapi_mcp import FastApiMCP

app = ServiceApp("My Service")

# Auto-expose all endpoints as MCP tools
mcp = FastApiMCP(
    app.get_app(),
    name="My Service MCP",
    base_url="http://localhost:8080"
)
mcp.mount()  # Mounts at /mcp
```

### Approach 3: Native MCP SDK

**What:** Use official MCP Python SDK directly

**Pros:**
- ✅ Full control
- ✅ No extra dependencies
- ✅ Official implementation

**Cons:**
- ⚠️ More boilerplate
- ⚠️ Steeper learning curve
- ⚠️ More code to maintain

### Approach 4: Hybrid (Recommended for PraisonAI-SVC)

**What:** Combine FastMCP with custom logic

**Pros:**
- ✅ Best of both worlds
- ✅ Flexibility + simplicity
- ✅ Gradual adoption

**Implementation:** See [Recommended Architecture](#recommended-architecture)

---

## Recommended Architecture

### Dual-Mode Operation

```
┌─────────────────────────────────────────┐
│         PraisonAI Service               │
│                                         │
│  ┌──────────────┐  ┌─────────────────┐ │
│  │   FastAPI    │  │    FastMCP      │ │
│  │   (REST)     │  │    (MCP)        │ │
│  └──────┬───────┘  └────────┬────────┘ │
│         │                   │          │
│         └───────┬───────────┘          │
│                 ▼                       │
│         ┌──────────────┐               │
│         │  Core Logic  │               │
│         │  (Shared)    │               │
│         └──────────────┘               │
└─────────────────────────────────────────┘
```

### File Structure

```
praisonai-svc/
├── src/praisonai_svc/
│   ├── __init__.py
│   ├── app.py              # FastAPI app
│   ├── mcp_server.py       # NEW: MCP server
│   ├── core.py             # NEW: Shared logic
│   ├── worker.py
│   ├── models/
│   └── azure/
```

### One-File Usage (Preserved)

```python
# app.py - User's service file
from praisonai_svc import ServiceApp

app = ServiceApp("My Service", enable_mcp=True)  # NEW: MCP flag

@app.job
def process(payload: dict) -> tuple[bytes, str, str]:
    return (data, "text/plain", "result.txt")

# Automatically exposed as MCP tool!

if __name__ == "__main__":
    app.run()  # Runs both FastAPI + MCP
```

### Transport Options

MCP supports multiple transports:

| Transport | Use Case | Deployment |
|-----------|----------|------------|
| **stdio** | Local CLI tools | `python app.py` |
| **StreamableHTTP** | Web/remote access | Azure Container Apps |
| **SSE** (deprecated) | Legacy support | Not recommended |

**Recommendation:** Support both stdio (local) and StreamableHTTP (production)

---

## Implementation Plan

### Phase 1: Core MCP Integration (Week 1)

**Goal:** Add basic MCP server alongside existing FastAPI

**Tasks:**

1. **Add FastMCP dependency**
   ```toml
   # pyproject.toml
   dependencies = [
       "fastmcp>=2.0.0",
       # ... existing deps
   ]
   ```

2. **Create MCP server module** (`mcp_server.py`)
   ```python
   from fastmcp import FastMCP, Context
   from praisonai_svc.models import JobRequest
   
   def create_mcp_server(service_app) -> FastMCP:
       mcp = FastMCP(service_app.service_name)
       
       @mcp.tool()
       async def create_job(payload: dict, ctx: Context) -> dict:
           """Create a new processing job"""
           await ctx.info(f"Creating job with payload: {payload}")
           # Delegate to existing logic
           job_id = await service_app.create_job_internal(payload)
           return {"job_id": job_id, "status": "queued"}
       
       @mcp.tool()
       async def get_job_status(job_id: str) -> dict:
           """Get job processing status"""
           job = await service_app.table_storage.get_job(job_id)
           return job.to_response().dict()
       
       @mcp.resource("jobs://recent")
       async def recent_jobs() -> str:
           """List recent jobs"""
           jobs = await service_app.table_storage.list_recent(10)
           return json.dumps([j.to_response().dict() for j in jobs])
       
       return mcp
   ```

3. **Integrate with ServiceApp**
   ```python
   # app.py
   class ServiceApp:
       def __init__(self, service_name: str, enable_mcp: bool = False):
           self.service_name = service_name
           self.app = FastAPI(...)
           
           if enable_mcp:
               from praisonai_svc.mcp_server import create_mcp_server
               self.mcp = create_mcp_server(self)
           else:
               self.mcp = None
       
       def run(self, host="0.0.0.0", port=8080):
           if self.mcp:
               # Run both FastAPI + MCP
               self._run_dual_mode(host, port)
           else:
               # Run FastAPI only
               uvicorn.run(self.app, host=host, port=port)
   ```

4. **Add transport support**
   - stdio for local testing
   - StreamableHTTP endpoint at `/mcp`

5. **Write tests**
   - Test MCP tool discovery
   - Test tool invocation
   - Test resource access

### Phase 2: Enhanced MCP Features (Week 2)

**Goal:** Add resources, prompts, and progress tracking

**Tasks:**

1. **Add Resources**
   ```python
   @mcp.resource("jobs://{job_id}/logs")
   async def job_logs(job_id: str) -> str:
       """Get job processing logs"""
       return await get_logs(job_id)
   
   @mcp.resource("system://health")
   async def system_health() -> str:
       """System health metrics"""
       return json.dumps({
           "status": "healthy",
           "queue_size": await queue.size(),
           "active_workers": worker_count()
       })
   ```

2. **Add Prompts**
   ```python
   @mcp.prompt()
   def analyze_job(job_id: str) -> str:
       """Generate job analysis prompt"""
       job = get_job(job_id)
       return f"Analyze this job: {job.to_json()}"
   ```

3. **Progress Tracking via MCP Context**
   ```python
   @mcp.tool()
   async def create_job_with_progress(payload: dict, ctx: Context):
       job_id = create_job(payload)
       await ctx.report_progress(0, 100, "Job queued")
       # Worker updates progress
       return {"job_id": job_id}
   ```

### Phase 3: Documentation & Examples (Week 3)

**Goal:** Make MCP adoption easy

**Tasks:**

1. **Update README** with MCP examples
2. **Create MCP examples**
   - `examples/mcp-chatbot/` - Text-based MCP service
   - `examples/mcp-ppt/` - File generation with MCP
3. **Add MCP testing guide**
4. **Create video tutorial**

### Phase 4: Production Features (Week 4)

**Goal:** Enterprise-ready MCP

**Tasks:**

1. **Add OAuth support** (via FastMCP)
2. **Add rate limiting** for MCP endpoints
3. **Add monitoring** for MCP tool calls
4. **Performance optimization**
5. **Security hardening**

---

## Migration Strategy

### For Existing Users

**No breaking changes:**

```python
# Old code (still works)
app = ServiceApp("My Service")

@app.job
def process(payload): ...

app.run()
```

**Opt-in to MCP:**

```python
# New code (MCP enabled)
app = ServiceApp("My Service", enable_mcp=True)

@app.job
def process(payload): ...

app.run()  # Now runs FastAPI + MCP
```

### Gradual Adoption Path

1. **Phase 1:** Enable MCP flag, no code changes
2. **Phase 2:** Add custom MCP tools/resources
3. **Phase 3:** Use MCP-specific features (prompts, context)

---

## Benefits & Use Cases

### Benefits

**For Service Developers:**
- ✅ AI agents can use your service automatically
- ✅ No need to write AI integration code
- ✅ Self-documenting API
- ✅ Type-safe interactions
- ✅ Built-in progress tracking

**For End Users:**
- ✅ Natural language interaction
- ✅ No API documentation needed
- ✅ Contextual help from AI
- ✅ Automated workflows

### Use Cases

**1. AI-Powered PPT Generation**
```
User: "Create a presentation about Q4 results"
Claude: [Discovers create_presentation tool]
Claude: [Calls tool with structured data]
Claude: "Done! Here's your presentation with charts and analysis."
```

**2. Automated Report Generation**
```
User: "Generate monthly report for all completed jobs"
Claude: [Reads jobs://recent resource]
Claude: [Calls generate_report tool]
Claude: [Monitors progress via context]
Claude: "Report ready with 42 jobs analyzed."
```

**3. Debugging Assistant**
```
User: "Why did job abc123 fail?"
Claude: [Reads jobs://abc123/logs resource]
Claude: [Analyzes error patterns]
Claude: "The job failed due to timeout. Here's how to fix it..."
```

---

## Technical Specifications

### MCP Server Configuration

```python
# config.py
class MCPConfig(BaseModel):
    enabled: bool = False
    transport: str = "stdio"  # or "http"
    http_endpoint: str = "/mcp"
    oauth_enabled: bool = False
    rate_limit: int = 100  # requests per minute
```

### Tool Schema Example

```json
{
  "name": "create_job",
  "description": "Create a new processing job",
  "inputSchema": {
    "type": "object",
    "properties": {
      "payload": {
        "type": "object",
        "description": "Job configuration and data"
      }
    },
    "required": ["payload"]
  }
}
```

### Resource URI Patterns

```
jobs://recent                    # List recent jobs
jobs://{job_id}                  # Specific job details
jobs://{job_id}/logs             # Job logs
jobs://{job_id}/result           # Job result
system://health                  # System health
system://stats                   # System statistics
```

---

## Testing Strategy

### MCP Inspector

```bash
# Test MCP server locally
fastmcp dev app.py

# Opens inspector at http://localhost:5173
# Test tools, resources, prompts interactively
```

### Integration Tests

```python
# tests/test_mcp.py
async def test_mcp_tool_discovery():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        assert "create_job" in [t.name for t in tools]

async def test_mcp_tool_call():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "create_job",
            {"payload": {"title": "Test"}}
        )
        assert "job_id" in result
```

---

## Deployment

### Local Development

```bash
# stdio transport
python app.py

# MCP client connects via stdin/stdout
```

### Production (Azure Container Apps)

```bash
# StreamableHTTP transport
# MCP endpoint at https://your-app.azurecontainerapps.io/mcp

# Clients connect via HTTP POST
curl -X POST https://your-app.azurecontainerapps.io/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

---

## Conclusion

Making PraisonAI-SVC **MCP-compatible** transforms it from a REST API service into an **AI-native platform** that can be seamlessly integrated with Claude, ChatGPT, and other LLM-powered applications.

**Key Advantages:**
- ✅ Maintains one-file simplicity
- ✅ Backward compatible
- ✅ AI agents can discover and use services automatically
- ✅ Self-documenting
- ✅ Production-ready with FastMCP

**Next Steps:**
1. Review this plan
2. Approve MCP integration approach
3. Begin Phase 1 implementation
4. Iterate based on feedback

---

**Document Version:** 1.0  
**Last Updated:** November 5, 2025  
**Author:** PraisonAI Team  
**Status:** Ready for Review
