# Creating Custom Langfun Actions: Best Practices Guide

This guide provides best practices for developing custom actions with Langfun, based on practical implementation experiences with FileSystem and Web Search actions.

## Key Implementation Requirements

### 1. Proper Module Structure and Imports

```python
from typing import Any, Optional, List, Dict, Literal, ClassVar
import os
import traceback
import langfun as lf
from langfun.core.agentic import action as action_lib
import pyglove as pg
```

- **Critical**: Import `action_lib` from `langfun.core.agentic`, not just `Action`
- Always include `pyglove` for symbolic programming support
- Use specific typing imports for better code clarity

### 2. Class Definition

```python
class MyAction(action_lib.Action):
    """Docstring describing the action's purpose and usage."""
    
    # Allow attribute modifications at runtime
    allow_symbolic_assignment = True
    
    # Define parameters with proper typing
    operation: Literal["op1", "op2"] = "op1"
    param1: Optional[str] = None
    param2: Optional[int] = 5
    
    # Class variables for default values
    default_value: ClassVar[str] = "/tmp"
```

- Inherit from `action_lib.Action`, not just `Action`
- **Important**: Set `allow_symbolic_assignment = True` to enable runtime attribute modification
- Use type annotations with `Literal` for constrained values
- Document parameters with clear comments
- Use `ClassVar` for class-level constants

### 3. Initialization and Parameter Validation

```python
def _on_bound(self):
    """Initialize and validate parameters."""
    super()._on_bound()  # Always call parent first
    
    # Set default values
    if not self.param1:
        self.param1 = self.default_value
        
    # Validate parameters
    self._validate_parameters()

def _validate_parameters(self):
    """Validate parameters are consistent."""
    if self.operation == "op1" and not self.param1:
        raise ValueError("param1 is required for op1 operation")
```

- **Always** call `super()._on_bound()` first
- Separate validation into a dedicated method for clarity
- Provide specific error messages with parameter details
- Set defaults in `_on_bound` rather than the call method

### 4. Call Method Signature

```python
def call(self, session, *, lm=None, **kwargs):
    """Execute the operation.
    
    Args:
        session: The current session context
        lm: Language model (required by interface)
        **kwargs: Additional keyword arguments
        
    Returns:
        Operation results
    """
    try:
        session.info(f"Starting {self.operation}")
        result = self._execute_operation()
        session.info(f"Completed {self.operation}")
        return result
        
    except Exception as e:
        error_msg = f"Failed to execute {self.operation}: {str(e)}"
        session.error(error_msg)
        session.error(traceback.format_exc())
        raise RuntimeError(error_msg) from e
```

- The signature **must** be: `def call(self, session, *, lm=None, **kwargs):`
- The `lm` parameter is required even if unused
- Parameters must be keyword-only (note the `*,` syntax)
- Use session logging for operation tracking
- Implement proper exception handling with traceback
- Re-raise exceptions with context
- Delegate actual work to helper methods

## Common Pitfalls and Solutions

### 1. WritePermissionError When Modifying Attributes

**Problem:**
```
CodeError: WritePermissionError: Cannot set attribute of <class FileSystemAction> 
while `FileSystemAction.allow_symbolic_assignment` is set to False
```

**Solution:**
Add `allow_symbolic_assignment = True` as a class variable.

### 2. Session Usage Errors

**Problem:**
```
Error: Execution already stopped.
```

**Solution:**
Create a new session for each action invocation:
```python
# Create a fresh session for each action
new_session = action_lib.Session()
result = action(session=new_session, lm=model)
```

### 3. Missing Arguments in Call Method

**Problem:**
```
TypeError: call() missing 1 required keyword-only argument: 'lm'
```

**Solution:**
Always include the `lm` parameter in the call signature and when invoking the action:
```python
result = action(session=session, lm=None)  # lm=None is valid
```

### 4. Session Attribute Access Errors

**Problem:**
```
AttributeError: 'Session' object has no attribute 'all_logs'
```

**Solution:**
Check for attribute existence before accessing:
```python
if hasattr(session, 'all_logs'):
    logs = session.all_logs
elif hasattr(session, 'logs'):
    logs = session.logs()
```

## Testing Strategies

### 1. Basic Unit Tests

```python
import unittest
from unittest.mock import patch, MagicMock
from your_module import YourAction

class TestYourAction(unittest.TestCase):
    def test_parameter_validation(self):
        # Test required parameters
        with self.assertRaises(ValueError):
            action = YourAction(operation="op1", param1=None)
            
    @patch('your_module.some_external_service')
    def test_operation(self, mock_service):
        # Mock external dependencies
        mock_service.return_value = "mock_result"
        
        # Create a mock session
        mock_session = MagicMock()
        
        # Create and execute the action
        action = YourAction(operation="op1", param1="test")
        result = action(session=mock_session, lm=None)
        
        # Verify results
        self.assertEqual(result, "expected_result")
        mock_session.info.assert_called()  # Verify logging
```

- Test parameter validation thoroughly
- Mock external dependencies (APIs, file system)
- Create mock sessions for testing
- Verify logging and error handling

### 2. Testing Web-based Actions

For actions that interact with external services:

```python
@patch('requests.get')
def test_api_call(self, mock_get):
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.json.return_value = {"items": [{"title": "Test", "link": "https://example.com"}]}
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response
    
    # Test the action
    action = SearchAction(query="test")
    results = action(session=MagicMock(), lm=None)
    
    # Verify results
    self.assertEqual(results[0]["title"], "Test")
```

- Mock HTTP responses to avoid actual network calls
- Test error handling for API failures
- Verify proper parsing of response data

## API Integration Best Practices

When integrating with external APIs:

1. **Always provide fallback mechanisms:**
   ```python
   def _execute_operation(self):
       if self.api_key:
           return self._api_method()
       else:
           return self._fallback_method()
   ```

2. **Handle API-specific errors:**
   ```python
   try:
       response = requests.get(self.api_url, params)
       response.raise_for_status()  # Check for HTTP errors
       return response.json()
   except requests.exceptions.HTTPError as e:
       if e.response.status_code == 429:
           # Handle rate limiting
           raise RuntimeError("API rate limit exceeded") from e
       raise RuntimeError(f"API error: {str(e)}") from e
   ```

3. **Use environment variables for credentials:**
   ```python
   api_key = os.environ.get('API_KEY')
   ```

## Real-world Usage Examples

### Example 1: FileSystem Action

```python
import langfun as lf
from FileSystem import FileSystemAction

# Create a model
model = lf.llms.OpenAI(model="gpt-4")

# Read file contents
read_action = FileSystemAction(
    operation="read",
    source_path="/path/to/file.txt"
)
content = read_action(lm=model)
```

### Example 2: Web Search Action

```python
from SearchAction import SearchAction
import os
from dotenv import load_dotenv

# Load API credentials
load_dotenv()
api_key = os.environ.get('GOOGLE_API_KEY')
cx_id = os.environ.get('GOOGLE_CX_ID')

# Create a new session
from langfun.core.agentic import action as action_lib
session = action_lib.Session()

# Perform a Google search
search_action = SearchAction(
    operation="google_search",
    query="langfun python framework",
    num_results=5,
    api_key=api_key,
    cx_id=cx_id
)
results = search_action(session=session, lm=None)

# Extract text from a webpage
extract_action = SearchAction(
    operation="extract_text",
    url="https://example.com"
)
# Create a new session for each action to avoid "Execution already stopped" errors
text = extract_action(session=action_lib.Session(), lm=None)
```

## Summary of Critical Requirements

1. **Correct imports and inheritance:** `from langfun.core.agentic import action as action_lib`
2. **Enable attribute assignment:** `allow_symbolic_assignment = True`
3. **Correct call method signature:** `def call(self, session, *, lm=None, **kwargs):`
4. **Create new sessions** for each action invocation
5. **Always call `super()._on_bound()`** in the initialization method
6. **Implement proper error handling** with specific error messages
7. **Use session logging** for tracking operations
8. **Provide fallback mechanisms** for external dependencies

By following these best practices, you'll create robust, maintainable Langfun actions that integrate well with the framework and handle errors gracefully.