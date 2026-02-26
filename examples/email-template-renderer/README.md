# Email Template Renderer Service

A service that renders email templates with dynamic data using Jinja2 templating engine.

## Features

- ✅ Render HTML email templates
- ✅ Render plain text email templates
- ✅ Support for Jinja2 templating syntax
- ✅ Variable substitution
- ✅ Template inheritance support
- ✅ Multiple output formats (HTML, Text, JSON)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

Create `.env` file:

```bash
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;"
```

### 3. Start Azurite (Azure Storage Emulator)

```bash
azurite --silent
```

### 4. Run the Service

```bash
python app.py
```

## Usage Examples

### Render HTML Email Template

```bash
curl -X POST http://localhost:8082/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "template": "<h1>Hello {{ name }}!</h1><p>Welcome to {{ company }}.</p><p>Your account balance is ${{ balance }}.</p>",
      "template_type": "html",
      "data": {
        "name": "John Doe",
        "company": "Acme Corp",
        "balance": 1250.50
      },
      "subject": "Welcome Email",
      "output_format": "html"
    }
  }'
```

### Render Text Email Template

```bash
curl -X POST http://localhost:8082/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "template": "Hello {{ name }}!\n\nWelcome to {{ company }}.\n\nYour account balance is ${{ balance }}.",
      "template_type": "text",
      "data": {
        "name": "Jane Smith",
        "company": "Tech Inc",
        "balance": 2500.00
      },
      "subject": "Account Information",
      "output_format": "text"
    }
  }'
```

### Render Template with Loops and Conditionals

```bash
curl -X POST http://localhost:8082/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "template": "<h1>Order Confirmation</h1><p>Hello {{ customer_name }},</p><p>Your order #{{ order_id }} includes:</p><ul>{% for item in items %}<li>{{ item.name }} - ${{ item.price }}</li>{% endfor %}</ul><p>Total: ${{ total }}</p>",
      "template_type": "html",
      "data": {
        "customer_name": "Alice Johnson",
        "order_id": "ORD-12345",
        "items": [
          {"name": "Product A", "price": 29.99},
          {"name": "Product B", "price": 49.99}
        ],
        "total": 79.98
      },
      "subject": "Order Confirmation",
      "output_format": "html"
    }
  }'
```

### Get JSON Output with Metadata

```bash
curl -X POST http://localhost:8082/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "template": "<h1>Hello {{ name }}!</h1>",
      "template_type": "html",
      "data": {"name": "John"},
      "subject": "Test Email",
      "output_format": "json"
    }
  }'
```

## Supported Template Features

### Variables

```jinja2
{{ variable_name }}
```

### Filters

```jinja2
{{ name|upper }}
{{ price|round(2) }}
{{ description|truncate(50) }}
```

### Conditionals

```jinja2
{% if condition %}
    Content when true
{% else %}
    Content when false
{% endif %}
```

### Loops

```jinja2
{% for item in items %}
    {{ item.name }}
{% endfor %}
```

## Output Formats

| Format | Output | Content Type |
|--------|--------|--------------|
| `html` | HTML email | text/html |
| `text` | Plain text email | text/plain |
| `json` | JSON with metadata | application/json |

## Payload Structure

```json
{
  "template": "Template content with {{ variables }}",
  "template_type": "html|text",
  "data": {
    "variable1": "value1",
    "variable2": "value2"
  },
  "subject": "Email subject (optional)",
  "output_format": "html|text|json"
}
```

## Complete Workflow

```bash
# 1. Create job
JOB_ID=$(curl -s -X POST http://localhost:8082/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "template": "<h1>Hello {{ name }}!</h1>",
      "data": {"name": "World"},
      "output_format": "html"
    }
  }' | jq -r .job_id)

# 2. Wait for processing
sleep 3

# 3. Check status
curl http://localhost:8082/jobs/$JOB_ID

# 4. Download result
curl http://localhost:8082/jobs/$JOB_ID/content -o email.html
```

## License

MIT License



