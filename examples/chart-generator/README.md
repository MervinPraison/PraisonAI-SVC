# Chart Generator Service

A service that generates charts from data using Matplotlib.

## Features

- ✅ Line charts
- ✅ Bar charts
- ✅ Pie charts
- ✅ Scatter plots
- ✅ Area charts
- ✅ Multiple series support
- ✅ Customizable styling and colors
- ✅ PNG output format

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

### Generate Bar Chart

```bash
curl -X POST http://localhost:8083/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "data": {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
        "values": [100, 150, 120, 180, 200]
      },
      "chart_type": "bar",
      "options": {
        "title": "Monthly Sales",
        "xlabel": "Month",
        "ylabel": "Sales ($)",
        "width": 10,
        "height": 6
      },
      "format": "png"
    }
  }'
```

### Generate Line Chart

```bash
curl -X POST http://localhost:8083/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "data": {
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "values": [450, 520, 480, 600]
      },
      "chart_type": "line",
      "options": {
        "title": "Quarterly Revenue",
        "xlabel": "Quarter",
        "ylabel": "Revenue ($1000)",
        "width": 10,
        "height": 6
      },
      "format": "png"
    }
  }'
```

### Generate Pie Chart

```bash
curl -X POST http://localhost:8083/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "data": {
        "labels": ["Desktop", "Mobile", "Tablet", "Other"],
        "values": [45, 30, 15, 10]
      },
      "chart_type": "pie",
      "options": {
        "title": "Device Usage Distribution",
        "width": 8,
        "height": 8
      },
      "format": "png"
    }
  }'
```

### Generate Multi-Series Bar Chart

```bash
curl -X POST http://localhost:8083/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "data": {
        "labels": ["Product A", "Product B", "Product C"],
        "datasets": [
          {
            "label": "2022",
            "values": [100, 150, 120]
          },
          {
            "label": "2023",
            "values": [120, 180, 140]
          }
        ]
      },
      "chart_type": "bar",
      "options": {
        "title": "Product Sales Comparison",
        "xlabel": "Product",
        "ylabel": "Sales ($1000)",
        "width": 10,
        "height": 6
      },
      "format": "png"
    }
  }'
```

### Generate Scatter Plot

```bash
curl -X POST http://localhost:8083/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "data": {
        "labels": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "values": [2, 4, 3, 5, 6, 7, 8, 9, 10, 11]
      },
      "chart_type": "scatter",
      "options": {
        "title": "Correlation Analysis",
        "xlabel": "X Axis",
        "ylabel": "Y Axis",
        "width": 10,
        "height": 6
      },
      "format": "png"
    }
  }'
```

### Generate Area Chart

```bash
curl -X POST http://localhost:8083/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "data": {
        "labels": ["Jan", "Feb", "Mar", "Apr", "May"],
        "values": [100, 150, 120, 180, 200]
      },
      "chart_type": "area",
      "options": {
        "title": "Monthly Growth",
        "xlabel": "Month",
        "ylabel": "Value",
        "width": 10,
        "height": 6
      },
      "format": "png"
    }
  }'
```

## Supported Chart Types

| Chart Type | Description | Data Structure |
|------------|-------------|----------------|
| `line` | Line chart | labels, values or datasets |
| `bar` | Bar chart | labels, values or datasets |
| `pie` | Pie chart | labels, values |
| `scatter` | Scatter plot | labels, values or datasets with x/y |
| `area` | Area chart | labels, values or datasets |

## Chart Options

```json
{
  "title": "Chart Title",
  "xlabel": "X Axis Label",
  "ylabel": "Y Axis Label",
  "width": 10,
  "height": 6,
  "dpi": 100,
  "style": "default|dark|seaborn",
  "colors": ["#FF5733", "#33FF57", "#3357FF"]
}
```

## Data Structure

### Simple Chart

```json
{
  "labels": ["Label1", "Label2", "Label3"],
  "values": [10, 20, 30]
}
```

### Multi-Series Chart

```json
{
  "labels": ["Label1", "Label2", "Label3"],
  "datasets": [
    {
      "label": "Series 1",
      "values": [10, 20, 30]
    },
    {
      "label": "Series 2",
      "values": [15, 25, 35]
    }
  ]
}
```

### Scatter Plot Data

```json
{
  "labels": [1, 2, 3, 4, 5],
  "values": [2, 4, 3, 5, 6]
}
```

Or with datasets:

```json
{
  "datasets": [
    {
      "label": "Series 1",
      "x": [1, 2, 3, 4, 5],
      "y": [2, 4, 3, 5, 6]
    }
  ]
}
```

## Complete Workflow

```bash
# 1. Create job
JOB_ID=$(curl -s -X POST http://localhost:8083/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "data": {
        "labels": ["A", "B", "C"],
        "values": [10, 20, 30]
      },
      "chart_type": "bar",
      "options": {"title": "Test Chart"}
    }
  }' | jq -r .job_id)

# 2. Wait for processing
sleep 3

# 3. Check status
curl http://localhost:8083/jobs/$JOB_ID

# 4. Download result
curl http://localhost:8083/jobs/$JOB_ID/content -o chart.png
```

## License

MIT License

