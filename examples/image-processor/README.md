# Image Processor Service

A service that processes images with various operations: resize, convert formats, apply filters, generate thumbnails, crop, and rotate.

## Features

- ✅ Resize images
- ✅ Convert formats (PNG, JPEG, WebP)
- ✅ Apply filters (grayscale, blur, brightness, contrast, sharpness)
- ✅ Generate thumbnails
- ✅ Crop images
- ✅ Rotate images

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

### Resize Image

```bash
python -c "import requests, json, base64; img = open('test.jpg', 'rb').read(); b64 = base64.b64encode(img).decode(); r = requests.post('http://localhost:8080/jobs', json={'payload': {'image_data': b64, 'operation': 'resize', 'width': 800, 'height': 600, 'format': 'jpeg'}}); print(json.dumps(r.json(), indent=2))"
```

### Apply Filter

```bash
python -c "import requests, json, base64; img = open('test.jpg', 'rb').read(); b64 = base64.b64encode(img).decode(); r = requests.post('http://localhost:8080/jobs', json={'payload': {'image_data': b64, 'operation': 'filter', 'filter_type': 'grayscale', 'format': 'png'}}); print(json.dumps(r.json(), indent=2))"
```

### Generate Thumbnail

```bash
python -c "import requests, json, base64; img = open('test.jpg', 'rb').read(); b64 = base64.b64encode(img).decode(); r = requests.post('http://localhost:8080/jobs', json={'payload': {'image_data': b64, 'operation': 'thumbnail', 'width': 200, 'height': 200, 'format': 'png'}}); print(json.dumps(r.json(), indent=2))"
```

## Supported Operations

| Operation | Description | Required Parameters |
|-----------|-------------|---------------------|
| `resize` | Resize image to specific dimensions | width, height |
| `convert` | Convert image format | format |
| `filter` | Apply image filters | filter_type |
| `thumbnail` | Generate thumbnail | width, height |
| `crop` | Crop image | width, height |
| `rotate` | Rotate image | angle |

## Supported Formats

- PNG
- JPEG/JPG
- WebP

## License

MIT License

