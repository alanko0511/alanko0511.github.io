---
name: explorer-api
description: How to use the local Cloudflare Explorer API at http://localhost:8787/cdn-cgi/explorer/api to inspect and manage KV, R2, D1, Durable Objects, and Workflows during local development. Use this skill whenever you need to inspect local Cloudflare state — listing KV keys, browsing R2 objects, querying D1, checking workflow instances, or debugging local storage. Also use when the user mentions "explorer API", "local bindings", or wants to see what's in their local KV/R2/D1/DO/Workflows.
---

# Cloudflare Local Explorer API

The Explorer API is a local-only REST API exposed by `wrangler dev` at `http://localhost:8787/cdn-cgi/explorer/api`. It provides direct access to the local state of Cloudflare bindings (KV, R2, D1, Durable Objects, Workflows) without going through your Worker's application code.

Use `curl` via the Bash tool to interact with it. All endpoints return JSON with a standard envelope:

```json
{
  "success": true,
  "errors": [],
  "messages": [],
  "result": ...,
  "result_info": { "count": N }
}
```

The dev server must be running (`wrangler dev` / `bun run dev`) for these endpoints to work.

## Discovering the API (Do This First)

The Explorer API serves its own OpenAPI schema. If you're unsure about an endpoint's parameters, request body, or response shape, fetch and parse the schema directly rather than guessing:

```bash
# List all available endpoints and methods
curl -s http://localhost:8787/cdn-cgi/explorer/api | python3 -c "
import json, sys
d = json.load(sys.stdin)
for path, ops in d['paths'].items():
    for method in ops:
        print(f'{method.upper()} {path}')
"

# Get full details for a specific endpoint (parameters, request body, responses)
curl -s http://localhost:8787/cdn-cgi/explorer/api | python3 -c "
import json, sys
d = json.load(sys.stdin)
target = '/r2/buckets/{bucket_name}/objects'  # change this
for method, details in d['paths'].get(target, {}).items():
    print(json.dumps({method.upper(): details}, indent=2))
"

# Search for endpoints by keyword
curl -s http://localhost:8787/cdn-cgi/explorer/api | python3 -c "
import json, sys
d = json.load(sys.stdin)
keyword = 'workflow'  # change this
for path, ops in d['paths'].items():
    if keyword.lower() in path.lower() or any(keyword.lower() in ops[m].get('summary','').lower() for m in ops):
        for method in ops:
            print(f'{method.upper()} {path} — {ops[method].get(\"summary\",\"\")}')
"
```

The schema is the source of truth — endpoints, parameters, and schemas can change across wrangler versions. Always consult it when you encounter unexpected behavior or need to use an endpoint not covered below.

## Discovery: What Bindings Exist?

Start with `GET /local/workers` to see all registered workers and their bindings. This tells you the binding names, IDs, and types available — use these IDs in subsequent calls.

```bash
curl -s http://localhost:8787/cdn-cgi/explorer/api/local/workers | python3 -m json.tool
```

The response includes a `bindings` object with `kv`, `r2`, `d1`, `do`, and `workflows` arrays, each containing the binding name and ID you need for further queries.

## KV

**List namespaces:**
```bash
curl -s http://localhost:8787/cdn-cgi/explorer/api/storage/kv/namespaces
```

**List keys** (use the namespace `id` from above):
```bash
curl -s "http://localhost:8787/cdn-cgi/explorer/api/storage/kv/namespaces/{namespace_id}/keys?limit=20"
```
- Supports `prefix` filtering and `cursor`-based pagination
- Response includes `expiration` (Unix timestamp) and `metadata` per key
- `result_info.cursor` is present when there are more pages

**Read a value:**
```bash
curl -s "http://localhost:8787/cdn-cgi/explorer/api/storage/kv/namespaces/{namespace_id}/values/{key_name}"
```
- Returns raw value bytes (not JSON-wrapped)
- Binary values will be binary — pipe to `head -c` or check content type
- URL-encode special characters in key names (`:` → `%3A`, `!` → `%21`)

**Bulk get** (POST, up to 100 keys):
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"keys":["key1","key2"]}' \
  "http://localhost:8787/cdn-cgi/explorer/api/storage/kv/namespaces/{namespace_id}/bulk/get"
```

## R2

**List buckets:**
```bash
curl -s http://localhost:8787/cdn-cgi/explorer/api/r2/buckets
```

**List objects** in a bucket:
```bash
curl -s "http://localhost:8787/cdn-cgi/explorer/api/r2/buckets/{bucket_name}/objects?prefix=maps/&per_page=20"
```
- Supports `prefix`, `delimiter`, `cursor`, and `per_page` (default 1000)
- Returns `key`, `etag`, `size`, `last_modified`, `http_metadata`, `custom_metadata`
- `result_info.is_truncated` indicates more pages; use `cursor` to paginate

**Get object metadata** (HEAD-like, without downloading the body):
```bash
curl -s -H "cf-metadata-only: true" \
  "http://localhost:8787/cdn-cgi/explorer/api/r2/buckets/{bucket_name}/objects/{url_encoded_key}"
```
- The object key path must be **URL-encoded** — slashes become `%2F`
  - Example: `maps/pmtiles/global/20260408.pmtiles` → `maps%2Fpmtiles%2Fglobal%2F20260408.pmtiles`
- Without the `cf-metadata-only` header, the full object body is returned

## D1

**List databases:**
```bash
curl -s http://localhost:8787/cdn-cgi/explorer/api/d1/database
```
- Optional `name` query param to filter

**Run a query** (POST):
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"sql":"SELECT * FROM my_table LIMIT 10","params":[]}' \
  "http://localhost:8787/cdn-cgi/explorer/api/d1/database/{database_id}/raw"
```
- Returns rows as arrays (not objects) for performance
- Use parameterized queries with `params` array

## Durable Objects

**List namespaces:**
```bash
curl -s http://localhost:8787/cdn-cgi/explorer/api/workers/durable_objects/namespaces
```

**List objects** in a namespace:
```bash
curl -s "http://localhost:8787/cdn-cgi/explorer/api/workers/durable_objects/namespaces/{id}/objects?limit=20"
```

**Query SQLite storage** (POST):
```bash
# By object ID:
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"objectId":"<hex-id>","sql":"SELECT * FROM _cf_KV"}' \
  "http://localhost:8787/cdn-cgi/explorer/api/workers/durable_objects/namespaces/{namespace_id}/query"

# By object name:
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"objectName":"my-object","sql":"SELECT * FROM _cf_KV"}' \
  "http://localhost:8787/cdn-cgi/explorer/api/workers/durable_objects/namespaces/{namespace_id}/query"
```

## Workflows

**List workflows:**
```bash
curl -s http://localhost:8787/cdn-cgi/explorer/api/workflows
```

**Get workflow details** (includes instance status counts):
```bash
curl -s "http://localhost:8787/cdn-cgi/explorer/api/workflows/{workflow_name}"
```

**List instances:**
```bash
curl -s "http://localhost:8787/cdn-cgi/explorer/api/workflows/{workflow_name}/instances?per_page=10"
```
- Filter by `status`: `queued`, `running`, `paused`, `errored`, `terminated`, `complete`, `waiting`, `waitingForPause`
- Paginate with `page` (1-indexed) and `per_page` (max 100)

**Get instance details** (includes params, steps with timing, outputs, and errors):
```bash
curl -s "http://localhost:8787/cdn-cgi/explorer/api/workflows/{workflow_name}/instances/{instance_id}"
```
- Shows each step's `name`, `start`/`end` times, `success`, `output`, retry config, and attempt history
- The `params` field shows the input the workflow was created with

## Gotchas

- **R2 object keys with slashes**: URL-encode the entire key in the path segment (`/` → `%2F`). The list endpoint returns keys with normal slashes, but the get/put endpoints need encoding.
- **KV values are raw**: The value endpoint returns the raw stored bytes, not a JSON envelope. Binary data (like PMTiles chunks) will be binary.
- **Pagination**: KV and DO use `cursor`-based pagination. R2 uses `cursor` + `is_truncated`. Workflows use `page`/`per_page`.
- **Dev server must be running**: All endpoints require `wrangler dev` to be active.
- **Large JSON responses**: The OpenAPI schema and some list responses are large single-line JSON blobs. Always pipe through `python3 -m json.tool` for readability, or use `python3 -c "import json, sys; ..."` to extract specific fields.
