# QR Code Generator Service

A service that generates QR codes from text, URLs, or contact information in multiple formats.

## Features

- ✅ Generate QR codes from any text or URL
- ✅ Multiple output formats (PNG, SVG)
- ✅ Customizable size and error correction
- ✅ Custom colors (fill and background)
- ✅ Adjustable border size

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment

Create `.env` file with Azure Storage connection string (see `.env.local` for template).

### 3. Run the Service

```bash
python app.py
```

## Usage Examples

### Generate QR Code from URL

```bash
python -c "import requests, json; r = requests.post('http://localhost:8080/jobs', json={'payload': {'data': 'https://example.com', 'format': 'png', 'size': 400, 'error_correction': 'H'}}); print(json.dumps(r.json(), indent=2))"
```

### Generate QR Code with Custom Colors

```bash
python -c "import requests, json; r = requests.post('http://localhost:8080/jobs', json={'payload': {'data': 'Hello World', 'format': 'png', 'size': 300, 'fill_color': '#0000FF', 'back_color': '#FFFFFF'}}); print(json.dumps(r.json(), indent=2))"
```

### Generate SVG QR Code

```bash
python -c "import requests, json; r = requests.post('http://localhost:8080/jobs', json={'payload': {'data': 'https://praison.ai', 'format': 'svg', 'size': 500}}); print(json.dumps(r.json(), indent=2))"
```

## Supported Formats

- PNG (default)
- SVG (requires qrcode[svg])

## Error Correction Levels

- `L` - Low (~7% error correction)
- `M` - Medium (~15% error correction) - Default
- `Q` - Quartile (~25% error correction)
- `H` - High (~30% error correction)

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `data` | string | required | Data to encode in QR code |
| `format` | string | "png" | Output format (png, svg) |
| `size` | integer | 300 | QR code size in pixels |
| `error_correction` | string | "M" | Error correction level (L, M, Q, H) |
| `border` | integer | 4 | Border size in boxes |
| `fill_color` | string | "#000000" | Fill color hex code |
| `back_color` | string | "#FFFFFF" | Background color hex code |

## License

MIT License

