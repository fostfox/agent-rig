# HTTP Repository Pattern — Implementation Details

Captured during PR #50 (issue-28-wave2) review fix session.

## 404→None Pattern

The `_call()` helper should check for 404 before `raise_for_status()`:

```python
async def _call(self, path: str, **kwargs) -> dict | None:
    resp = await self._client.post(f"/api/internal/bot/{path}", json=kwargs)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()
```

This keeps `if data else None` working in calling methods:

```python
async def get_user_by_id(self, user_id: UUID) -> User | None:
    data = await self._call("users/get-by-id", user_id=str(user_id))
    return User(**data) if data else None
```

## Missing Optional Fields in Deserialization

Domain models may not have all fields the router serializes. Example: `LinkCode`
lacks `updated_at`, but `model_dump()` on the router side doesn't include it,
causing `KeyError` when HttpRepo tries `data["updated_at"]`.

**Fix:** Use `.get()` for fields that may be absent:

```python
# Before (breaks):
updated_at=_from_iso(data["updated_at"])

# After (safe):
updated_at=_from_iso(data.get("updated_at"))
```

Also handle `None` in `_from_iso`:

```python
def _from_iso(iso_str: str | None) -> datetime | None:
    if iso_str is None:
        return None
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
```

## Route Path Alignment

HttpRepo's `_call` prefixes with `/api/internal/bot/` and uses nested-style paths
like `"users/get-by-id"`. The router must use matching paths:

```python
# HttpRepo side:
await self._call("users/get-by-id", user_id=str(user_id))
# → POST /api/internal/bot/users/get-by-id

# Router side:
router = APIRouter(prefix="/api/internal/bot")
@router.post("/users/get-by-id")  # matching path
```

## Token Auth: Fail Closed

When `TELEGRAM_BOT_TOKEN` is empty or unset, the auth check should reject:

```python
async def verify_token(authorization: str = Header(...)) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise HTTPException(status_code=403, detail="Bot token not configured")
    # ... rest of auth check
```

Without this, an empty env var leads to `provided == ""` matching `token == ""`,
accepting any request with `Authorization: Bearer `.

## Use AsyncClient, Not Client

The HttpRepo adapter runs in an async context (the bot uses `await`). Use
`httpx.AsyncClient` instead of the synchronous `httpx.Client`:

```python
class HttpRepo:
    def __init__(self, base_url: str, token: str):
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}", ...},
            timeout=30,
        )
```

## Shared Repo Instance (Not Per-Request)

The bot router should use a shared repository instance from DI rather than
creating a new `PostgresRepo()` per request. Each instance opens its own
asyncpg connection, leading to connection exhaustion:

```python
# BAD - creates new connection per request:
def get_repo():
    return PostgresRepo()

# GOOD - uses shared instance from DI:
def get_repo():
    from api.app.di import resolve_repo
    return resolve_repo()
```
