# API Reference

## Core Endpoints

### Chat Endpoint

```http
POST /chat
Content-Type: application/json

{
    "messages": [
        {
            "role": "user",
            "content": "string"
        }
    ],
    "model": "string"
}
```

**Response**
```json
{
    "messages": [
        {
            "role": "assistant",
            "content": "string",
            "tool_calls": []
        }
    ],
    "requires_confirmation": null,
    "error": null
}
```

### Upload Endpoint

```http
POST /upload
Content-Type: multipart/form-data

file: binary
```

### Confirmation Endpoint

```http
POST /confirm
Content-Type: application/json

{
    "confirmed": boolean,
    "action_details": {
        "prompt": "string",
        "tool_name": "string",
        "tool_args": {}
    }
}
```

## Authentication

Currently uses API key authentication through environment variables.

## Rate Limiting

- Standard: 60 requests per minute
- Authenticated: 100 requests per minute

## Error Codes

| Code | Description |
|------|-------------|
| 400  | Bad Request |
| 401  | Unauthorized |
| 429  | Too Many Requests |
| 500  | Server Error |
