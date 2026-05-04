# Menu Reader

HTTP microservice that receives images of restaurant menus and returns structured JSON with categories, items, descriptions, prices, currencies, and promotions, using LLM Vision with a multi-provider interface (OpenAI, Anthropic, Gemini).

## Features

- Stack: Python 3.11+, FastAPI, Pydantic v2.
- Pluggable multi-provider LLM (OpenAI, Anthropic, Google Gemini).
- Structured output validated with Pydantic.
- Single or batch extraction support.
- Image rescaling and validation.
- Automatic retries with backoff.
- Docker container ready.

## Requirements

- Python 3.11 or higher.
- `uv` (recommended) or `pip`.
- At least one API key from the supported providers.

## Installation

```bash
uv sync
cp .env.example .env
```

Edit `.env` and add at least one API key.

## Run (development)

```bash
uv run fastapi dev
```

Interactive documentation will be available at `http://localhost:8000/docs`.

## Run (production)

```bash
uv run fastapi run
```

## Docker

```bash
docker build -t menu-reader .
docker run -p 8000:8000 --env-file .env menu-reader
```

## Endpoints

| Method | Path                    | Description                                     |
| ------ | ----------------------- | ----------------------------------------------- |
| POST   | `/api/v1/extract`       | Processes an image and returns `ExtractedMenu`. |
| POST   | `/api/v1/extract/batch` | Processes multiple images in parallel.          |
| GET    | `/health`               | Service status and configured providers.        |
| GET    | `/docs`                 | Swagger UI.                                     |

### Authentication

All routes under `/api/v1` require the `X-API-Key` header with the value configured in `API_KEY` inside the `.env` file. The `/health` route remains public for availability checks.

```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@menu.jpg" \
  -H "X-API-Key: $API_KEY"
```

Error codes:

- `401 Unauthorized`: the header is missing or its value does not match.
- `503 Service Unavailable`: the `API_KEY` variable is not configured on the server.

### Provider selection

Via query param or HTTP header. If not specified, `DEFAULT_PROVIDER` is used.

```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@menu.jpg" \
  -H "X-API-Key: $API_KEY" \
  -H "X-LLM-Provider: anthropic"
```

```bash
curl -X POST "http://localhost:8000/api/v1/extract?provider=gemini" \
  -F "file=@menu.jpg" \
  -H "X-API-Key: $API_KEY"
```

### Force currency in the response

The optional `currency` query param overrides the detected currency on items, variants, and promotions. If omitted, the currency detected by the LLM is preserved.

Supported values (ISO 4217): `USD`, `EUR`, `ARS`, `BOB`, `BRL`, `CLP`, `COP`, `CRC`, `CUP`, `DOP`, `GTQ`, `HNL`, `HTG`, `MXN`, `NIO`, `PAB`, `PEN`, `PYG`, `UYU`, `VES`, `UNKNOWN`.

```bash
curl -X POST "http://localhost:8000/api/v1/extract?currency=ARS" \
  -F "file=@menu.jpg" \
  -H "X-API-Key: $API_KEY"
```

### Example response

```json
{
  "metadata": {
    "restaurant_name": "All Grill",
    "phone": "0424.209.87.56",
    "payment_methods": ["Pago Movil"]
  },
  "categories": [
    {
      "name": "Parrillas",
      "items": [
        { "name": "Mix", "description": "Carne y Pollo, acompanado de yuca o bollito", "price": "4320", "currency": "VES", "variants": [] }
      ]
    }
  ],
  "promotions": [
    {
      "name": "2 Jumbos + 1 Refresco de Litro",
      "description": null,
      "includes": ["2 Jumbos", "1 Refresco de Litro"],
      "price": "2700",
      "currency": "VES"
    }
  ],
  "notes": null
}
```

## Tests

```bash
uv run pytest
```

To run the E2E tests against real APIs (requires keys to be configured):

```bash
uv run pytest -m live
```
