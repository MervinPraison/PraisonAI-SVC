# PraisonAI Service Framework - Examples

This directory contains example applications demonstrating the PraisonAI Service Framework.

## Available Examples

### 1. Text Processor Service 🆕

**Location:** `text-processor-service/`

A comprehensive, production-ready example demonstrating all features of the framework.

**Features:**
- ✅ 7 text processing operations
- ✅ 3 output formats (TXT, JSON, Markdown)
- ✅ Complete test suite (25+ tests)
- ✅ Full documentation (2000+ lines)
- ✅ Cross-platform support (Windows/Linux/Mac)
- ✅ Docker support
- ✅ Setup automation

**Quick Start:**
```bash
cd text-processor-service
bash setup.sh        # Linux/Mac
# OR
setup.bat            # Windows

python app.py
```

**Documentation:**
- 📖 [README.md](text-processor-service/README.md) - Complete guide
- 🚀 [QUICKSTART.md](text-processor-service/QUICKSTART.md) - 5-minute setup
- 💻 [EXAMPLES.md](text-processor-service/EXAMPLES.md) - Usage examples
- 📋 [SUMMARY.md](text-processor-service/SUMMARY.md) - Quick overview

**What You'll Learn:**
- How to implement the `@app.job` decorator
- How to process different types of payloads
- How to return different file types
- How to test your service locally
- How to deploy to production

### 2. PPT Service

**Location:** `ppt-service/`

Simple example for PowerPoint generation.

**Status:** Template/stub implementation

**Quick Start:**
```bash
cd ppt-service
python app.py
```

## Recommended Learning Path

### Beginner
1. **Start with:** `text-processor-service/QUICKSTART.md`
2. **Try:** Run the quick test
3. **Explore:** `text-processor-service/app.py`

### Intermediate
1. **Read:** `text-processor-service/README.md`
2. **Run:** Unit tests and workflow tests
3. **Modify:** Add your own text operations

### Advanced
1. **Study:** Complete implementation in `text-processor-service/`
2. **Create:** Your own service based on the template
3. **Deploy:** To Azure Container Apps

## Creating Your Own Service

### Option 1: Use the CLI

```bash
praisonai-svc new my-service
cd my-service
python app.py
```

### Option 2: Copy the Template

```bash
cp -r text-processor-service my-service
cd my-service
# Modify app.py for your use case
```

### Option 3: Start from Scratch

```python
from praisonai_svc import ServiceApp

app = ServiceApp("My Service")

@app.job
def process_job(payload: dict) -> tuple[bytes, str, str]:
    # Your logic here
    result = f"Processed: {payload}"
    return result.encode(), "text/plain", "result.txt"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

## Common Use Cases

### Document Processing
```python
@app.job
def process_document(payload: dict) -> tuple[bytes, str, str]:
    # Convert, analyze, or transform documents
    return pdf_bytes, "application/pdf", "output.pdf"
```

### Image Processing
```python
@app.job
def process_image(payload: dict) -> tuple[bytes, str, str]:
    # Resize, filter, or analyze images
    return image_bytes, "image/png", "output.png"
```

### Data Analysis
```python
@app.job
def analyze_data(payload: dict) -> tuple[bytes, str, str]:
    # Analyze data and generate reports
    return csv_bytes, "text/csv", "report.csv"
```

### API Integration
```python
@app.job
def call_external_api(payload: dict) -> tuple[bytes, str, str]:
    # Call external APIs and aggregate results
    return json_bytes, "application/json", "result.json"
```

## Testing Your Service

### Local Testing with Azurite

1. Install Azurite:
   ```bash
   npm install -g azurite
   ```

2. Start Azurite:
   ```bash
   azurite --silent
   ```

3. Configure `.env`:
   ```bash
   PRAISONAI_AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
   ```

### Using Real Azure Storage

1. Create Storage Account in Azure Portal
2. Get connection string from "Access Keys"
3. Update `.env` with your connection string

## Example Comparison

| Feature | Text Processor | PPT Service |
|---------|----------------|-------------|
| Operations | 7 | 1 |
| Output Formats | 3 | 1 |
| Tests | 25+ | 0 |
| Documentation | Complete | Minimal |
| Production Ready | ✅ Yes | ⚠️ Template |
| Recommended For | Learning & Production | Quick Start |

## Directory Structure

```
examples/
├── README.md                    (this file)
│
├── text-processor-service/      ⭐ Recommended
│   ├── app.py                   - Main application
│   ├── test_app.py              - Unit tests
│   ├── test_workflow.sh         - Integration tests
│   ├── README.md                - Complete guide
│   ├── QUICKSTART.md            - Quick setup
│   ├── EXAMPLES.md              - Usage examples
│   ├── SUMMARY.md               - Overview
│   ├── Dockerfile               - Container config
│   ├── requirements.txt         - Dependencies
│   ├── setup.sh / setup.bat     - Setup scripts
│   ├── quick-test.py/.sh        - Quick tests
│   └── start.bat                - Start script (Windows)
│
└── ppt-service/
    └── app.py                   - PowerPoint example
```

## Additional Resources

### Documentation
- [Main README](../README.md) - Framework overview
- [PRD](../PRD.md) - Product requirements
- [Deployment Guide](../DEPLOYMENT.md) - Production deployment

### Links
- [GitHub Repository](https://github.com/MervinPraison/PraisonAI-SVC)
- [Issue Tracker](https://github.com/MervinPraison/PraisonAI-SVC/issues)
- [PraisonAI Website](https://praison.ai)

## Contributing Examples

Have a great example? Contribute it!

1. Create a new directory with your example
2. Include:
   - `app.py` - Main application
   - `README.md` - Documentation
   - `requirements.txt` - Dependencies
   - `test_*.py` - Tests (optional)
3. Submit a pull request

## Support

- **Quick Questions**: See example documentation
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## License

All examples are MIT licensed.

---

**Start with:** [`text-processor-service/QUICKSTART.md`](text-processor-service/QUICKSTART.md)

