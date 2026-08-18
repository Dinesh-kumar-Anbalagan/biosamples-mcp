# BioSamples MCP Server

A Model Context Protocol (MCP) server for interacting with the EMBL-EBI BioSamples service through structured, reusable tools.

The server provides operations for discovering server capabilities, searching existing BioSamples records, retrieving a sample by accession, and submitting a user-confirmed BioSamples payload. It uses an asynchronous HTTP adapter for BioSamples API communication, middleware-based request processing, dependency injection, Redis-backed caching, and Redis-backed authentication token lookup for protected submission operations.

## Features

- Search existing BioSamples records using text queries and structured filters.
- Retrieve an individual sample using a BioSamples accession.
- Submit a prepared BioSamples-compatible sample payload.
- Require a user-provided Webin ID before submission.
- Retrieve submission authentication tokens from Redis.
- Return an authentication-required response when no cached token is available.
- Cache read-only tool responses using Redis.
- Skip response caching for submission operations.
- Continue read-only requests when the Redis response cache is unavailable.
- Provide structured logging around tool execution and API requests.
- Dynamically discover and register MCP tools.
- Resolve tool dependencies using `dependency-injector`.
- Use asynchronous HTTP requests through `httpx`.

## Architecture

```text
MCP Client / AI Assistant
          |
          v
+-----------------------------+
|      FastMCP Server         |
|  Dynamic Tool Registration  |
+-------------+---------------+
              |
              v
+-----------------------------+
|     MCP Tool Orchestrator   |
+-------------+---------------+
              |
              v
+-----------------------------+
|     Execution Pipeline      |
|                             |
|  1. Logging Middleware      |
|  2. Authentication          |
|  3. Redis Cache             |
+-------------+---------------+
              |
              v
+-----------------------------+
|        Tool Services        |
|                             |
|  - Server Info              |
|  - Search Samples           |
|  - Get Sample               |
|  - Submit Sample            |
+-------------+---------------+
              |
              v
+-----------------------------+
|     BioSamples Adapter      |
|     async HTTP / httpx      |
+-------------+---------------+
              |
              v
       EMBL-EBI BioSamples
              API

Submission authentication flow:

User provides Webin ID
          |
          v
biosamples_submitsample
          |
          v
Redis token lookup
      /         \
 token found   token missing
     |             |
     v             v
BioSamples POST   authentication_required
                 + localhost login URL
```

## Available MCP Tools

| Tool | Purpose | Operation |
|---|---|---|
| `biosamples_serverinfo` | Returns server name, version, and supported tools | Read-only |
| `biosamples_searchsamples` | Searches BioSamples using text, filters, date range, and pagination | Read-only |
| `biosamples_getsample` | Retrieves one sample using its accession | Read-only |
| `biosamples_submitsample` | Submits a prepared BioSamples-compatible sample | Write |

## Tool Usage

### 1. Server Information

Tool:

```text
biosamples_serverinfo
```

Input:

```json
{}
```

Example response:

```json
{
  "serverName": "BioSamples MCP Server",
  "version": "0.1.0",
  "supportedTools": [
    "biosamples_serverinfo",
    "biosamples_submitsample",
    "biosamples_searchsamples",
    "biosamples_getsample"
  ]
}
```

### 2. Search Samples

Tool:

```text
biosamples_searchsamples
```

The `query` field is required. Filters, date range, page, and size are optional.

Example:

```json
{
  "query": "human blood diabetes",
  "filters": [
    {
      "type": "attr",
      "field": "organism",
      "value": "Homo sapiens"
    }
  ],
  "page": 0,
  "size": 10
}
```

Supported structured filter types:

| Type | Purpose | Example |
|---|---|---|
| `attr` | Attribute | `attr:organism:Homo sapiens` |
| `acc` | Accession | `acc:SAMN*` |
| `rel` | Relationship | `rel:derivedFrom:SAMEA123` |
| `rrel` | Reverse relationship | `rrel:derivedFrom:SAMEA123` |
| `dom` | Domain | `dom:self.BioSamples` |
| `name` | Sample name | `name:sample one` |
| `extd` | External reference | `extd:ENA:ERR123` |

Date filtering is passed separately using `dateRange`:

```json
{
  "query": "liver",
  "dateRange": {
    "field": "release",
    "from": "2024-01-01",
    "until": "2026-08-01"
  },
  "page": 0,
  "size": 10
}
```

A date range is translated into a BioSamples date filter such as:

```text
dt:release:from=2024-01-01until=2026-08-01
```

### 3. Get Sample by Accession

Tool:

```text
biosamples_getsample
```

Example input:

```json
{
  "accession": "SAMN12345678"
}
```

The tool retrieves the corresponding sample from the BioSamples API and returns it under the `sample` field.

### 4. Submit Sample

Tool:

```text
biosamples_submitsample
```

Submission is a write operation and requires both:

- `webinId`
- `submissionSample`

Example:

```json
{
  "webinId": "Webin-12345",
  "submissionSample": {
    "name": "human blood diabetes sample",
    "release": "2026-08-01T00:00:00",
    "characteristics": {
      "organism": [
        {
          "text": "Homo sapiens"
        }
      ],
      "material": [
        {
          "text": "blood"
        }
      ],
      "disease": [
        {
          "text": "diabetes"
        }
      ]
    }
  }
}
```

The submission payload should already be complete, reviewed, and ready for the BioSamples API before this tool is called.

## Authentication Flow

`biosamples_submitsample` is the protected tool.

The MCP server requires the caller to provide a non-empty `webinId`. The server hashes that ID to create a Redis lookup key and checks Redis for a previously stored authentication token.

If a token is available, the server sends the sample to BioSamples with:

```http
Authorization: Bearer <token>
```

If no token is available, the tool returns an authentication-required response similar to:

```json
{
  "status": "authentication_required",
  "message": "Authentication is required before submitting the sample.",
  "loginUrl": "http://localhost:8080/login"
}
```

The localhost URL is intended for a companion authentication service running in the user's environment. That login application is not implemented inside this repository.

If Redis itself cannot be reached during the submission authentication lookup, the tool returns a service-unavailable response and asks the user to contact the system administrator.

## Redis Caching

Redis is used for response caching when caching is enabled.

Default cache TTL:

```text
300 seconds
```

The following tool is deliberately excluded from response caching because it performs a write operation:

```text
biosamples_submitsample
```

For read-only operations, cache keys are generated from the tool name and request payload using SHA-256.

If Redis is unavailable during a normal read-only cache operation, the request continues without cache and returns the live result.

## Project Structure

```text
biosamples-mcp/
├── src/
│   ├── adapter/
│   │   └── bio_samples_adapter.py
│   ├── app/
│   │   └── bootstrap.py
│   ├── core/
│   │   ├── config.py
│   │   ├── decorators.py
│   │   ├── logger.py
│   │   └── redis_client.py
│   ├── domain/
│   │   ├── bio_samples_api_error.py
│   │   └── filter_builder.py
│   ├── mcp_loader/
│   │   ├── container_builder.py
│   │   ├── dynamic_tool_loader.py
│   │   └── server.py
│   ├── middleware/
│   │   ├── base/
│   │   │   └── tool_middleware.py
│   │   ├── auth_middleware.py
│   │   ├── cache_middleware.py
│   │   └── logging_middleware.py
│   ├── model/
│   │   └── bio_sample.py
│   ├── orchestrator/
│   │   ├── execution_pipeline.py
│   │   ├── mcp_tool_orchestrator.py
│   │   ├── request_context.py
│   │   └── tool_executor.py
│   └── tools/
│       ├── base/
│       │   └── tool_service.py
│       ├── get_sample_tool_service.py
│       ├── search_samples_tool_service.py
│       ├── server_info_tool_service.py
│       └── submit_sample_tool_service.py
├── tests/
├── pyproject.toml
├── LICENSE
└── README.md
```

## Requirements

- Python 3.11 or later
- Redis for caching and submission authentication token lookup
- Network access to the configured BioSamples API

Main Python dependencies:

- `mcp`
- `httpx`
- `redis`
- `dependency-injector`

Development dependencies:

- `pytest`
- `pytest-asyncio`
- `ruff`
- `mypy`

## Installation

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd biosamples-mcp
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
.venv\Scripts\activate
```

Install the package with development dependencies:

```bash
pip install -e ".[dev]"
```

## Configuration

The server reads configuration from environment variables.

| Variable | Default | Description |
|---|---|---|
| `BIOSAMPLES_BASE_URL` | `https://wwwdev.ebi.ac.uk/biosamples` | BioSamples API base URL |
| `BIOSAMPLES_TIMEOUT_SECONDS` | `30` | HTTP request timeout in seconds |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `CACHE_TTL_SECONDS` | `300` | Redis response cache TTL |
| `CACHE_ENABLED` | `true` | Enables or disables response caching |

Example:

```bash
export BIOSAMPLES_BASE_URL="https://wwwdev.ebi.ac.uk/biosamples"
export BIOSAMPLES_TIMEOUT_SECONDS="30"
export REDIS_URL="redis://localhost:6379/0"
export CACHE_TTL_SECONDS="300"
export CACHE_ENABLED="true"
```

To run without response caching:

```bash
export CACHE_ENABLED="false"
```

Note that Redis is still required for the current submission authentication-token flow if `biosamples_submitsample` is used.

## Running Redis Locally

If Redis is installed locally:

```bash
redis-server
```

Verify it is available:

```bash
redis-cli ping
```

Expected response:

```text
PONG
```

## Running the MCP Server

After installing the project:

```bash
python -m mcp_loader.server
```

The entry point creates the FastMCP server, dynamically loads components and tool services, constructs the execution pipeline, and registers discovered MCP tools.

## MCP Client Configuration

A stdio-based MCP client can launch the server using a configuration conceptually similar to:

```json
{
  "mcpServers": {
    "biosamples": {
      "command": "/absolute/path/to/biosamples-mcp/.venv/bin/python",
      "args": [
        "-m",
        "mcp_loader.server"
      ],
      "cwd": "/absolute/path/to/biosamples-mcp",
      "env": {
        "REDIS_URL": "redis://localhost:6379/0",
        "CACHE_ENABLED": "true"
      }
    }
  }
}
```

Client configuration formats vary between MCP clients, so adapt the command, working directory, and environment fields to the client being used.

## Middleware Pipeline

Requests pass through an execution pipeline before reaching the selected tool.

### Logging Middleware

Records tool start, completion, execution duration, request ID, and failures.

### Authentication Middleware

Allows read-only tools to execute anonymously and requires a `webinId` for `biosamples_submitsample`.

### Cache Middleware

Caches eligible tool responses in Redis and skips the submission tool.

The pipeline keeps tool-specific logic separate from cross-cutting concerns such as logging, authorization checks, and caching.

## Dynamic Tool Registration

Tool classes use the custom `@Tool` decorator to define:

- MCP tool name
- tool description
- JSON input schema

`ContainerBuilder` discovers registered components and tool classes, resolves constructor dependencies, and adds providers to a dynamic dependency-injection container.

`DynamicToolLoader` then converts each JSON schema into a Python function signature and registers the generated handler with FastMCP.

This design allows new tools to be added without manually registering every handler in the server entry point.

## Error Handling

BioSamples API errors are wrapped in `BioSamplesAPIError` and can include:

- HTTP status code
- request URL
- response preview
- retryability information

HTTP responses with status codes `500` or above are marked retryable by the adapter.

The middleware also logs unexpected execution failures while allowing the exception to propagate to the MCP layer.

## Testing

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run the complete test suite:

```bash
pytest
```

Current repository test result:

```text
66 passed
```

Run with concise output:

```bash
pytest -q
```

Run an individual test module:

```bash
pytest tests/tools/test_tool_services.py
```

## Code Quality

Run Ruff checks:

```bash
ruff check src tests
```

Format code with Ruff:

```bash
ruff format src tests
```

Run type checking:

```bash
mypy src
```

## Safety Considerations

The server separates read-only operations from submission operations.

`biosamples_searchsamples`, `biosamples_getsample`, and `biosamples_serverinfo` do not write BioSamples data.

`biosamples_submitsample` can create a real BioSamples record and should therefore only be used after the payload has been reviewed, required fields are present, the user has explicitly chosen to submit it, and a valid authentication token is available for the supplied Webin ID.

Never hard-code Webin credentials or JWTs in the repository.

## Extending the Server

A new MCP tool can follow the existing tool-service pattern:

1. Create a class that implements the tool service interface.
2. Add the `@Tool` decorator.
3. Define a unique tool name, description, and JSON input schema.
4. Add typed constructor dependencies when required.
5. Implement the asynchronous `execute()` method.
6. Add unit tests for the new service and any new adapter/domain behavior.

The dynamic loader will discover registered tools from the configured tool package.

## Current Scope

This repository currently implements the BioSamples-facing MCP layer for:

- server discovery
- sample search
- sample retrieval
- authenticated sample submission
- Redis response caching
- Redis authentication-token lookup
- structured middleware execution

Sample extraction from natural language, checklist-schema retrieval, checklist validation, and the web-based login portal are separate concerns and are not implemented in this repository version.

