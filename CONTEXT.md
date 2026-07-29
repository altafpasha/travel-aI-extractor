# Travel AI Extractor - Context & Development Roadmap

> Version: MVP v1
> Goal: Build the world's best AI engine for extracting travel destinations from screenshots, videos, captions, and social media content.

---

# Vision

People save hundreds of travel posts on Instagram, TikTok, YouTube and Reddit but never revisit them because organizing them into trips is difficult.

Our goal is to build an AI engine that understands travel content and extracts structured travel locations automatically.

This project is **NOT** a travel booking app.

This project is **NOT** a map application.

This project is an **AI Place Extraction Engine** that can later power:

- Travel Planner
- AI Itinerary Generator
- Travel CRM
- Browser Extensions
- Mobile Apps
- APIs
- Third-party integrations

---

# Core Problem

Users currently:

- Save Instagram Reels
- Save TikToks
- Take screenshots
- Save Reddit posts
- Watch YouTube travel videos

But later they cannot remember

- where the place was
- which city
- country
- attractions
- hotels
- restaurants

The AI should solve this automatically.

---

# Long Term Vision

```
Travel Content

↓

AI Understanding Engine

↓

Structured Places

↓

Trip Organization

↓

AI Itinerary

↓

Export Anywhere
```

Eventually this becomes the "GitHub Copilot for Travel."

---

# Tech Stack

Backend

- Python 3.12
- FastAPI
- AsyncIO

Database

- SQLite (MVP)
- PostgreSQL (Production)

Storage

- Local
- S3 compatible later

AI

- Gemini 2.5 Flash

Maps

- Google Places API

Video

- FFmpeg
- OpenCV

Testing

- Pytest

Deployment

- Docker
- Docker Compose

Infrastructure

- Existing VPS
- Nginx
- Redis (later)

---

# Development Philosophy

Build the smallest thing that works.

Never over engineer.

Every phase must produce something usable.

Only move to the next phase when the current one works well.

---

# Phase 1 — Project Foundation

Goal

Create a clean backend architecture.

Tasks

- Setup FastAPI
- Configure Docker
- Configure Docker Compose
- Create project structure
- Environment variables
- Logging
- Health endpoint
- Swagger docs
- GitHub Actions (optional)

Expected Result

```
GET /

returns

Travel AI Extractor Running
```

---

# Phase 2 — Image Extraction MVP

Goal

Extract travel places from screenshots and photos.

User uploads

- Screenshot
- Instagram image
- Photo

Pipeline

```
Image

↓

Gemini Vision

↓

Extract place names

↓

Google Places

↓

JSON
```

API

POST

```
/extract/image
```

Expected Response

```json
{
  "destination": "Kyoto",
  "places": [
    {
      "name": "Fushimi Inari Shrine",
      "city": "Kyoto",
      "country": "Japan",
      "confidence": 96
    }
  ]
}
```

Success Criteria

- Works consistently
- <10 seconds
- Accurate locations

---

# Phase 3 — Text Extraction

Goal

Understand travel captions.

Example

```
Spent the weekend exploring cafes around Kyoto and visited Fushimi Inari.
```

Pipeline

```
Text

↓

Gemini

↓

Places

↓

Google Places
```

Endpoint

```
POST /extract/text
```

---

# Phase 4 — Video Extraction

Goal

Extract travel places from videos.

Input

- MP4
- Reel download
- TikTok download

Pipeline

```
Video

↓

FFmpeg

↓

Frames

↓

Gemini Vision

↓

Merge Places

↓

Google Places

↓

JSON
```

Frame Strategy

One frame every 3 seconds.

Do not process every frame.

Success Criteria

- Supports videos up to 2 minutes.
- Efficient CPU usage.

---

# Phase 5 — Place Validation

AI may hallucinate.

Every extracted location must be verified.

Pipeline

```
AI Place

↓

Google Places

↓

Exists?

↓

YES

↓

Return

NO

↓

Discard
```

Store

- Place ID
- Coordinates
- Rating
- Address

---

# Phase 6 — Confidence Engine

Goal

Measure confidence instead of blindly trusting AI.

Signals

Vision

Caption

OCR

Speech

Google Match

Example

Vision

"Blue Lagoon"

Caption

"Blue Lagoon Iceland"

Google Match

Blue Lagoon Iceland

Confidence

99%

Another example

Vision

"Temple"

No caption

No speech

Confidence

45%

Only auto accept high confidence.

---

# Phase 7 — Smart Cache

Never process identical content twice.

Pipeline

```
Image

↓

SHA256

↓

Already processed?

↓

YES

↓

Return Cache

NO

↓

AI
```

Benefits

- Lower API cost
- Faster response
- Better scalability

---

# Phase 8 — OCR (Optional)

Use local OCR before AI.

Options

- Google ML Kit
- PaddleOCR

Pipeline

```
Image

↓

OCR

↓

Found text?

↓

YES

↓

Google Places

↓

DONE

NO

↓

Gemini Vision
```

This reduces Gemini API calls.

---

# Phase 9 — Speech Recognition

Videos contain valuable information.

Pipeline

```
Video

↓

Audio

↓

Speech

↓

Extract Place Names

↓

Merge
```

Future

- Faster Whisper
- Whisper API

---

# Phase 10 — Multi Source Engine

Every source becomes one internal format.

Supported

Instagram

TikTok

YouTube

Screenshots

Photos

Videos

Reddit

Pinterest

Output

```
TravelContent

caption

frames

ocr

speech

metadata
```

Everything uses one AI pipeline.

---

# Phase 11 — AI Memory

Store extracted places.

Example

User imported

20 Bali reels.

AI remembers

- Beach Clubs
- Cafes
- Hotels
- Waterfalls

Later

User asks

"Show me all waterfalls."

AI already knows.

---

# Phase 12 — Trip Builder

Convert saved places into trips.

Example

```
Japan

↓

Kyoto

↓

2 Days

↓

AI Groups Places

↓

Itinerary
```

Output

Morning

Lunch

Evening

Hotels

Restaurants

---

# Phase 13 — AI Chat

Examples

"Build me a 5-day Japan itinerary."

"Which saved cafes are near Shibuya?"

"What are the best beaches from my Bali saves?"

---

# Phase 14 — Mobile App

React Native

Expo

Features

- Upload
- Share Sheet
- Saved Trips
- Search
- Maps
- Offline Cache

---

# Phase 15 — Social Import

Future

Instagram

TikTok

Pinterest

YouTube

Browser Extension

Share Sheet

---

# API Structure

```
POST /extract/image

POST /extract/video

POST /extract/text

GET /places

GET /health

GET /cache

DELETE /cache
```

---

# Folder Structure

```
travel-ai-extractor/

app/

routers/

services/

models/

schemas/

database/

utils/

uploads/

cache/

tests/

docker/

docs/
```

---

# Coding Standards

- Async everywhere
- Typed Python
- Pydantic models
- Modular services
- No business logic inside routers
- Services are reusable
- Repository pattern for database
- Environment variables only
- Comprehensive logging

---

# Testing Strategy

Every feature must include tests.

Unit Tests

- AI parser
- Confidence engine
- Place validator

Integration Tests

- Image upload
- Video upload
- Text extraction

Performance Tests

- Response time
- Memory usage
- CPU usage

---

# Success Metrics

Phase 2

- Image extraction accuracy >85%

Phase 4

- Video extraction works under 15 seconds

Phase 6

- Confidence score correlates with accuracy

Phase 7

- Cache hit rate >40%

Phase 12

- AI itinerary quality validated by users

---

# Future SaaS Vision

This engine should eventually expose APIs for developers.

Example

```
POST /api/extract

↓

Upload image

↓

Return structured travel places
```

Potential products

- Mobile App
- Web Dashboard
- Browser Extension
- Chrome Extension
- AI Travel Assistant
- Public API
- Enterprise Travel Intelligence Platform

---

# Guiding Principle

Focus on solving **one problem exceptionally well**:

> Transform unstructured travel inspiration into structured, searchable, and actionable travel destinations using AI.

Everything else—trip planning, itineraries, collaboration, and monetization—should be built only after the extraction engine is reliable, accurate, and fast.