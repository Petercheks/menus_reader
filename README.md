# Menu Reader

Microservicio HTTP que recibe imagenes de menus de restaurantes y devuelve un JSON estructurado con categorias, items, descripciones, precios, monedas y promociones, usando LLM Vision con interfaz multi-proveedor (OpenAI, Anthropic, Gemini).

## Caracteristicas

- Stack: Python 3.11+, FastAPI, Pydantic v2.
- Multi-proveedor LLM intercambiable (OpenAI, Anthropic, Google Gemini).
- Salida estructurada validada con Pydantic.
- Soporte de extraccion individual o por lotes.
- Reescalado y validacion de imagenes.
- Reintentos automaticos con backoff.
- Listo para contenedor Docker.

## Requisitos

- Python 3.11 o superior.
- `uv` (recomendado) o `pip`.
- Al menos una API key de los proveedores soportados.

## Instalacion

```bash
uv sync
cp .env.example .env
```

Edita `.env` y agrega al menos una API key.

## Ejecucion (desarrollo)

```bash
uv run fastapi dev
```

La documentacion interactiva estara en `http://localhost:8000/docs`.

## Ejecucion (produccion)

```bash
uv run fastapi run
```

## Docker

```bash
docker build -t menu-reader .
docker run -p 8000:8000 --env-file .env menu-reader
```

## Endpoints

| Metodo | Ruta                    | Descripcion                                  |
| ------ | ----------------------- | -------------------------------------------- |
| POST   | `/api/v1/extract`       | Procesa una imagen y devuelve `ExtractedMenu`. |
| POST   | `/api/v1/extract/batch` | Procesa multiples imagenes en paralelo.      |
| GET    | `/health`               | Estado del servicio y proveedores configurados. |
| GET    | `/docs`                 | Swagger UI.                                  |

### Autenticacion

Todas las rutas bajo `/api/v1` requieren el header `X-API-Key` con el valor configurado en `API_KEY` dentro del archivo `.env`. La ruta `/health` queda publica para chequeos de disponibilidad.

```bash
curl -X POST http://localhost:8000/api/v1/extract \
  -F "file=@menu.jpg" \
  -H "X-API-Key: $API_KEY"
```

Codigos de error:

- `401 Unauthorized`: el header falta o el valor no coincide.
- `503 Service Unavailable`: la variable `API_KEY` no esta configurada en el servidor.

### Seleccion de proveedor

Por query param o header HTTP. Si no se especifica, se usa `DEFAULT_PROVIDER`.

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

### Forzar moneda en la respuesta

El query param opcional `currency` permite sobreescribir la moneda detectada en items, variantes y promociones. Si se omite, se conserva la moneda detectada por el LLM.

Valores soportados (ISO 4217): `USD`, `EUR`, `ARS`, `BOB`, `BRL`, `CLP`, `COP`, `CRC`, `CUP`, `DOP`, `GTQ`, `HNL`, `HTG`, `MXN`, `NIO`, `PAB`, `PEN`, `PYG`, `UYU`, `VES`, `UNKNOWN`.

```bash
curl -X POST "http://localhost:8000/api/v1/extract?currency=ARS" \
  -F "file=@menu.jpg" \
  -H "X-API-Key: $API_KEY"
```

### Ejemplo de respuesta

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

Para ejecutar los tests E2E con APIs reales (requiere keys configuradas):

```bash
uv run pytest -m live
```
