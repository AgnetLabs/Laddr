# Tool Development Guide

Tools are functions that agents can call to interact with external systems, perform calculations, or access data.  
The `@tool` decorator registers a Python function as an agent tool with proper schema and tracing.

---

## Basic Tool Structure

```python
from laddr import tool
from typing import Dict

@tool(
    name="weather_lookup",
    description="Fetches current weather for a given city",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"},
            "units": {"type": "string", "description": "Units (metric/imperial)", "default": "metric"}
        },
        "required": ["city"]
    }
)
def weather_lookup(city: str, units: str = "metric") -> Dict:
    """Tool docstring: fetch current weather."""
    try:
        result = get_weather(city, units)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

---

## The `@tool` Decorator

**Syntax:**
```python
@tool(
    name: str,
    description: str,
    parameters: dict,
    trace: bool = True,
    trace_mask: list = []
)
```

---

## Key Features

| Parameter | Type | Required | Description |
|------------|------|-----------|-------------|
| name | str | ✅ | Unique identifier used by agents |
| description | str | ✅ | Summary of the tool’s purpose |
| parameters | dict | ✅ | JSON Schema for tool inputs |
| trace | bool | ❌ | Enables or disables logging |
| trace_mask | list | ❌ | Redacts sensitive trace fields |

---

### Parameter Descriptions

#### `name`

**Rules:**
- Must be unique and descriptive  
- Use lowercase `snake_case`  
- Avoid generic names  

**Examples:**
```python
name="web_search"
name="calculate_area"
name="query_database"
```

---

#### `description`

**Best Practices:**
- Begin with an action verb  
- Limit to 100 characters  
- Avoid redundant phrasing like “use this tool to…”  

**Examples:**
```python
description="Scrape text content from a webpage"
description="Translate text from English to French"
```

---

#### `parameters`

Each tool defines a **JSON Schema** describing its accepted parameters.

**Example:**
```python
parameters={
    "type": "object",
    "properties": {
        "url": {"type": "string", "description": "Page URL"},
        "timeout": {"type": "integer", "description": "Timeout seconds", "default": 10}
    },
    "required": ["url"]
}
```

**Supported JSON Schema Types:**

| Type | Description | Example |
|------|--------------|---------|
| string | Text input | `"hello"` |
| integer | Whole numbers | `42` |
| number | Decimals | `3.14` |
| boolean | True/False | `true` |
| array | Lists | `["a", "b"]` |
| object | Nested dict | `{"key": "value"}` |

---

#### `trace`

Enables or disables trace logging.

**Example:**
```python
trace=True  # Default
```

Set to `False` when:
- Handling sensitive user data  
- Reducing log volume for high-frequency tools  

---

#### `trace_mask`

Redacts specified fields in traces.

**Example:**
```python
trace_mask=["api_key", "token", "password"]
```

Fields matching these keys will appear as:
```
***REDACTED***
```
in logs.

---

## Example Tool Patterns

### Pattern 1: API Wrapper

```python
@tool(name="api_call", description="Perform a GET request to external API")
def api_call(endpoint: str) -> Dict:
    api_key = os.getenv("API_KEY")
    response = requests.get(
        f"https://api.example.com/{endpoint}",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10
    )
    return {"status": "success", "data": response.json()}
```

---

### Pattern 2: Data Transformer

```python
@tool(name="convert_format", description="Convert data between formats")
def convert_format(data: str, to_format: str = "json") -> Dict:
    if to_format == "json":
        return {"result": json.loads(data)}
    elif to_format == "csv":
        return {"result": parse_csv(data)}
    else:
        return {"error": f"Unsupported format {to_format}"}
```

---

### Pattern 3: File Operations

```python
@tool(name="list_files", description="List files by pattern")
def list_files(directory: str, pattern: str = "*") -> Dict:
    import glob
    files = glob.glob(f"{directory}/{pattern}")
    return {"files": files, "count": len(files)}
```

---

## Registering Tools with Agents

Tools must be passed to an agent during instantiation:

```python
from laddr import Agent
from tools.web_tools import web_search
from tools.math_tools import calculate

agent = Agent(
    name="researcher",
    tools=[web_search, calculate]
)
```

Agents automatically load the tool schemas and metadata for decision-making.

---

## Testing Tools

### Manual Testing (Python)
```python
from tools.web_tools import web_search

result = web_search(query="AI trends", max_results=3)
print(result)
```

### Manual Testing (API)
```bash
curl -X POST http://localhost:8000/api/agents/researcher/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "search for AI trends"}'
```
