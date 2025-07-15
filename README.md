# Image Room Classification Service

A Flask-based image classification service that uses Gemini AI to determine whether images are rooms and provide structured descriptions.

## Features

- 🏠 Uses Gemini 2.5 Pro AI model for image analysis
- 📥 Supports downloading images from URLs
- 🔍 Accurately determines if images are rooms
- 🚀 RESTful API interface
- 📊 Detailed logging
- ✅ Health check endpoint
- 🏗️ Structured room descriptions with room type, basic info, and features

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
python run.py
```

The service will start at `http://localhost:5000`

## API Usage

### 1. Analyze Images for Room Classification

**Endpoint:** `POST /analyze_room`

**Request Format:**

**Single Image:**

```json
{
  "url": "https://example.com/image.jpg",
  "include_description": true
}
```

**Multiple Images (URL Array):**

```json
{
  "url": [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    "https://example.com/image3.jpg"
  ],
  "include_description": false
}
```

**Parameters:**
- `url` (required): Image URL or array of image URLs
- `include_description` (optional): Whether to include detailed description in response. Default: `true`
  - `true`: Returns both `is_room` and `description` fields
  - `false`: Returns only `is_room` field (faster response, less data)

**Response Format:**

**Single Image:**

```json
{
  "success": true,
  "total": 1,
  "results": [
    {
      "url": "https://example.com/image.jpg",
      "success": true,
      "is_room": true,
      "description": {
        "room_type": "客厅",
        "basic_info": "Modern open-plan living space with neutral tones and natural lighting",
        "features": "Large windows provide abundant natural light and city views"
      }
    }
  ]
}
```

**Multiple Images:**

```json
{
  "success": true,
  "total": 3,
  "results": [
    {
      "url": "https://example.com/image1.jpg",
      "success": true,
      "is_room": true,
      "description": {
        "room_type": "客厅",
        "basic_info": "Modern living room with open layout",
        "features": "Spacious design with large windows"
      }
    },
    {
      "url": "https://example.com/image2.jpg",
      "success": true,
      "is_room": false,
      "description": {
        "room_type": "",
        "basic_info": "",
        "features": ""
      }
    },
    {
      "url": "https://example.com/image3.jpg",
      "success": false,
      "error": "Failed to download image"
    }
  ]
}
```

### 2. Health Check

**Endpoint:** `GET /health`

**Response Format:**

```json
{
  "status": "healthy",
  "service": "image-room-classifier"
}
```

## Examples

### Using curl

```bash
# Analyze single room image (with description)
curl -X POST http://localhost:5000/analyze_room \
  -H "Content-Type: application/json" \
  -d '{"url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "include_description": true}'

# Analyze single room image (without description - faster)
curl -X POST http://localhost:5000/analyze_room \
  -H "Content-Type: application/json" \
  -d '{"url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800", "include_description": false}'

# Analyze multiple images (without description)
curl -X POST http://localhost:5000/analyze_room \
  -H "Content-Type: application/json" \
  -d '{"url": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"], "include_description": false}'

# Health check
curl http://localhost:5000/health
```

### Using Python

```python
import requests

# Analyze single image
response = requests.post('http://localhost:5000/analyze_room',
                        json={'url': 'https://example.com/image.jpg'})
result = response.json()
print(f"Is room: {result['results'][0]['is_room']}")

# Analyze multiple images
urls = [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    "https://example.com/image3.jpg"
]
response = requests.post('http://localhost:5000/analyze_room', json={'url': urls})
result = response.json()

for i, item in enumerate(result['results']):
    if item['success']:
        print(f"Image {i+1}: {'Room' if item['is_room'] else 'Not a room'}")
        if item['is_room']:
            desc = item['description']
            print(f"  Room type: {desc['room_type']}")
            print(f"  Basic info: {desc['basic_info']}")
            print(f"  Features: {desc['features']}")
    else:
        print(f"Image {i+1}: Analysis failed - {item['error']}")
```

## Room Definition

According to the system prompt, a room is defined as:

- An interior space within a building
- Intended for human occupancy or activity
- Examples: living rooms, bedrooms, kitchens, offices, bathrooms, studies, etc.

## Room Types

The service can classify rooms into the following types:

- 客厅 (Living Room)
- 家庭室 (Family Room)
- 餐厅 (Dining Room)
- 厨房 (Kitchen)
- 主卧室 (Master Bedroom)
- 卧室 (Bedroom)
- 客房 (Guest Room)
- 卫生间 (Bathroom)
- 浴室 (Bathroom)
- 书房 (Study)
- 家庭办公室 (Home Office)
- 洗衣房 (Laundry Room)
- 储藏室 (Storage Room)
- 食品储藏间 (Pantry)
- 玄关 (Entrance)
- 门厅 (Foyer)
- 走廊 (Corridor)
- 阳台 (Balcony)
- 地下室 (Basement)
- 阁楼 (Attic)
- 健身房 (Gym)
- 家庭影院 (Home Theater)
- 游戏室 (Game Room)
- 娱乐室 (Entertainment Room)
- 其他 (Other)

## Error Handling

The service returns detailed error information:

```json
{
  "success": false,
  "error": "Error description"
}
```

Common errors:

- Missing image URL parameter
- Empty image URL
- Failed to download image
- Image analysis failed
- SSL connection errors
- Unsupported MIME type

## Configuration

- Gemini API key is hardcoded in the application
- Service port: 5000
- Timeout: 30 seconds (image download)
- SSL verification: Disabled for compatibility

## Logging

The service logs detailed information including:

- Image download status
- Analysis process
- Error messages
- Request processing status

## Features

### Google Image Search Support

- Automatically extracts actual image URLs from Google image search URLs
- Handles SSL certificate issues
- Validates MIME types

### Structured Descriptions

Each room image analysis returns:

- **room_type**: Specific room classification from the predefined list
- **basic_info**: Concise description of overall style and layout
- **features**: One-sentence highlight of the most significant feature

### Batch Processing

- Supports analyzing multiple images in a single request
- Individual image failures don't affect other images
- Returns comprehensive results for all processed images
