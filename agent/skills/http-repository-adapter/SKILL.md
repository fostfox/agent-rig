---
name: http-repository-adapter
description: "HTTP DB adapter — Protocol over HTTP, no DSN."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, hexagonal, http, adapter, service-communication, security]
    related_skills: [plan, test-driven-development, e2e-with-stateful-mock]
---

# HTTP Repository Adapter Pattern

When two services need shared database access, the naive approach is giving both a DSN. This creates security surface (open ports, need for TLS, IP allowlists, credential distribution).

**Better:** Make the remote service call the API via HTTP. The API owns the database; the remote service gets an HTTP-based implementation of the same repository Protocol.

## Architecture

```
┌─────────────┐     HTTP + Bearer Token     ┌──────────────┐     asyncpg     ┌──────────┐
│  Bot (Vultr) │ ──────────────────────────> │  API (k3s)   │ ────────────> │ Postgres  │
│              │                             │              │               │          │
│  HttpRepo    │                             │  PostgresRepo│               │          │
└─────────────┘                             └──────────────┘               └──────────┘
     No DSN                                    Has DSN
     No asyncpg                                Connection pool
     No open ports
```

## Key Benefits

- **Zero open database ports** — Postgres listens only inside the cluster
- **No TLS certs for DB** — only HTTPS for the API
- **No IP allowlists** — no NodePort/LoadBalancer for Postgres
- **Auditable operations** — only explicitly implemented methods are callable
- **Bearer token auth** — simple, no DSN secrets on the remote machine
- **Hexagonal architecture preserved** — calling code doesn't know about transport

## Implementation Pattern

### 1. Protocol (shared/domain/ports.py)

```python
@runtime_checkable
class OrderRepository(Protocol):
    async def get_order_by_hash(self, order_hash: UUID) -> Optional[Order]: ...
    async def create_order(self, user_id: UUID) -> Order: ...
```

### 2. Local adapter (shared/infrastructure/postgres_repo.py)

```python
class PostgresRepo:
    """Implements OrderRepository via asyncpg — local/cluster-internal."""
    async def get_order_by_hash(self, order_hash: UUID) -> Order | None:
        row = await self._conn.fetchrow("SELECT * FROM orders WHERE order_hash = $1", order_hash)
        return self._row_to_order(row) if row else None
```

### 3. HTTP adapter (shared/infrastructure/http_repo.py)

```python
class HttpRepo:
    """Implements OrderRepository via HTTP calls to the API."""

    def __init__(self, base_url: str, token: str):
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
        )

    async def get_order_by_hash(self, order_hash: UUID) -> Order | None:
        resp = self._client.post("/orders/get-by-hash",
            json={"order_hash": str(order_hash)})
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return deserialize_order(resp.json())

    async def create_order(self, user_id: UUID) -> Order:
        resp = self._client.post("/orders/create",
            json={"user_id": str(user_id)})
        resp.raise_for_status()
        return deserialize_order(resp.json())
```

### 4. API router (api/app/bot_router.py)

```python
router = APIRouter(prefix="/internal/bot")

def _verify_token(auth: str = Header(...)):
    if auth != f"Bearer {settings.BOT_API_TOKEN}":
        raise HTTPException(401)

@router.post("/orders/get-by-hash")
async def get_order_by_hash(data: dict, repo=Depends(get_repo),
                            _=Depends(_verify_token)):
    order = await repo.get_order_by_hash(UUID(data["order_hash"]))
    if not order:
        raise HTTPException(404)
    return serialize_order(order)
```

### 5. DI swap (telegram_bot/app/di.py)

```python
# Before:
def get_repo():
    from shared.infrastructure.postgres_repo import PostgresRepo
    return PostgresRepo()

# After:
def get_repo():
    from shared.infrastructure.http_repo import HttpRepo
    return HttpRepo(
        base_url="https://app.fostfox.com/internal/bot",
        token=get_config().telegram_bot_token,
    )
```

## API Endpoint Design

Use POST with JSON body. Consistent naming:

```
POST /api/internal/bot/users/get-by-id
POST /api/internal/bot/users/get-by-session
POST /api/internal/bot/orders/get
POST /api/internal/bot/orders/get-by-hash
POST /api/internal/bot/orders/create
POST /api/internal/bot/orders/update-status
POST /api/internal/bot/models/get-by-order
POST /api/internal/bot/link-codes/get
POST /api/internal/bot/link-codes/consume
```

**Why not RESTful CRUD?** The caller is a program, not a browser. POST+JSON avoids HTTP verb mapping and query string issues.

## Testing

1. **Unit tests**: Test `HttpRepo` against a mock or the actual API
2. **Integration tests**: Run the API → point `HttpRepo` at it — tests pass against either implementation
3. **E2E tests**: On sandbox VM, use tg-mock + full stack. HttpRepo calls `http://api:8000/api/internal/bot/*`

Existing `test_bot.py` tests should pass unchanged — they test against the `OrderRepository` Protocol, not the implementation.

## Pitfalls

- **Serialization drift** — Use shared deserialization helpers between HttpRepo and the router.
- **Error handling** — HTTP 404 → None, HTTP errors → typed exceptions. No httpx leaks to domain code.
- **Auth token rotation** — Consider a separate BOT_API_TOKEN to decouple from TELEGRAM_BOT_TOKEN.
- **Latency** — ~1-5ms per call vs direct asyncpg. Add bulk endpoints if batch operations are common.
