# Langfun Action Development Prompt Template (Enhanced)

Use this template when requesting help with developing custom Langfun actions. The more details you provide, the more effective assistance you'll receive.

## 1. Action Purpose and Requirements

**Action Name**: [Provide a clear name for your action, e.g., "NotionAction", "FileSystemAction"]

**Primary Purpose**: 
[Describe what your action should accomplish in 1-2 sentences]

**Operations/Capabilities**:
- [List the specific operations/methods you want the action to support]
- [Example: "Read pages", "Create database entries", "Query resources"]
- [Consider both basic and advanced operations for completeness]

**Input Parameters**:
- [List the key parameters your action should accept]
- [Specify parameter types, defaults, and constraints]
- [Consider both direct identifiers (IDs) and convenient alternatives (URLs)]

**Output Expectations**:
- [Describe the expected return values]
- [Indicate if you want simplified/processed output vs. raw API responses]
- [Specify error response structures]

## 2. Environment Context

**Langfun Version**: [e.g., "latest", "1.2.3"]

**Python Version**: [e.g., "3.9", "3.10"]

**External Dependencies**:
- [List any external libraries or APIs your action needs]
- [Include version constraints if specific versions are required]
- [Example: "notion-client>=2.0.0", "requests"]

**API Keys/Authentication**:
- [Describe authentication requirements in detail]
- [Specify if multiple auth methods should be supported]
- [Example: "Support both direct token and environment variable auth"]

## 3. Implementation Details

**Class Structure**:
```python
# Provide any existing code or pseudocode if available
from langfun.core.agentic import action as action_lib

class MyAction(action_lib.Action):
    allow_symbolic_assignment = True
    
    # Define operations with Literal type
    operation: Literal["op1", "op2"] = "op1"
    
    # Define parameters with proper typing
    parameter1: Optional[str] = None
    parameter2: Optional[int] = None
    
    # Additional attributes or methods
    pass
```

**Error Handling Strategy**:
- [Specify how errors should be handled and returned]
- [Example: "Return structured error objects instead of raising exceptions"]
- [Describe any retry or fallback mechanisms]

**Parameter Validation Strategy**:
- [Describe how parameters should be validated]
- [Example: "Support URL extraction to automatically populate ID fields"]
- [Indicate which parameters are required vs. optional]

**Integration Points**:
- [Describe how this action will be used in your larger system]
- [Example: "Will be called by agents to access and modify Notion data"]

## 4. Challenges and Considerations

**Potential Issues**:
- [Describe any specific challenges you anticipate]
- [Example: "API rate limiting", "Handling pagination", "Complex data structures"]

**Backward Compatibility**:
- [Note any library version differences to handle]
- [Example: "Support both older and newer client library versions"]

**Performance Concerns**:
- [Mention any performance requirements]
- [Example: "Minimize API calls", "Handle large response volumes"]

**Specific Questions**:
- [List specific questions about implementation]
- [Example: "How should complex nested data be simplified?"]

## 5. Testing and Deployment

**Testing Strategy**:
- [Describe comprehensive testing approach]
- [Include unit tests, mocking strategy, and edge cases]
- [Example: "Need comprehensive unit tests with mocked API responses"]

**Documentation Requirements**:
- [Specify documentation needs]
- [Example: "Include detailed example usage in README"]

**Deployment Context**:
- [Explain where the action will be deployed]
- [Example: "Local development", "Production agent service"]

## 6. Learned Best Practices

**Error Handling Best Practices**:
- Return structured error objects instead of raising exceptions for easier client handling
- Include operation name, error message, and traceback in error responses
- Add runtime safeguards to prevent client errors (like recursion issues)

**Parameter Processing Best Practices**:
- Support multiple input formats (direct IDs, URLs, etc.) for user convenience
- Add helper methods to extract IDs from user-friendly inputs
- Include utility methods to simplify complex API responses

**Initialization Best Practices**:
- Set `allow_symbolic_assignment = True` for runtime attribute modification
- Handle API library version differences with try/except fallbacks
- Initialize with clear default values and validate parameters thoroughly

**Call Method Best Practices**:
- Always use signature: `def call(self, session, *, lm=None, **kwargs):`
- Implement proper session logging for debugging
- Return structured, consistent responses with simplified data

## Example for API Integration Action:

```
## 1. Action Purpose and Requirements

**Action Name**: NotionAction

**Primary Purpose**: 
Enable Langfun agents to interact with Notion workspace resources including pages, databases, and users.

**Operations/Capabilities**:
- Read, create, and update pages
- Query, create, and update databases
- Search across workspace
- List users in workspace
- Extract simplified page and database information

**Input Parameters**:
- operation: Type of operation to perform (read_page, update_page, etc.)
- page_id: Notion page identifier (optional if url provided)
- database_id: Notion database identifier (optional if url provided)
- url: Direct Notion URL to extract IDs automatically
- token: Notion API integration token
- properties: Page or database properties for create/update
- content: Page content or database schema
- query_filter: Filter criteria for database queries

**Output Expectations**:
- Pages: Structured object with page data and content
- Databases: Query results with simplified property values
- Info operations: Simplified metadata with human-readable values
- Errors: Structured objects with operation, message, and traceback

## 2. Environment Context

**Langfun Version**: latest

**Python Version**: 3.10+

**External Dependencies**:
- notion-client
- requests

**API Keys/Authentication**:
- Support both direct token parameter and NOTION_API_TOKEN environment variable
- Require Notion workspace integration with appropriate permissions

## 3. Implementation Details

**Class Structure**:
```python
class NotionAction(action_lib.Action):
    allow_symbolic_assignment = True
    
    # Define operations with Literal
    operation: Literal[
        "read_page", "create_page", "update_page", 
        "query_database", "create_database", "update_database",
        "search", "list_users", "get_page_info", "get_database_info"
    ] = "read_page"
    
    # Define parameters with proper typing
    page_id: Optional[str] = None
    database_id: Optional[str] = None
    url: Optional[str] = None
    token: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    content: Optional[List[Dict[str, Any]]] = None
    query_filter: Optional[Dict[str, Any]] = None
```

**Error Handling Strategy**:
- Return structured error objects with error message, operation name, and traceback
- Handle URL extraction failures gracefully
- Validate client initialization with helpful error messages
- Add extra validation checks in call() method before API operations

**Parameter Validation Strategy**:
- Extract page_id or database_id from URL automatically
- Support both direct IDs or URL parameter for convenience
- Handle API version differences with try/except patterns
- Provide utility methods to simplify complex Notion API objects

**Integration Points**:
- Will be used by agents to read and write Notion content
- Will simplify complex Notion API responses for agent consumption

## 4. Challenges and Considerations

**Potential Issues**:
- Notion API token management and permissions
- Handling various URL formats and ID extraction
- Supporting different versions of notion-client library
- Preventing infinite recursion during initialization

**Backward Compatibility**:
- Handle different client initialization patterns for various library versions
- Support both newer UUID format and older page ID formats

**Performance Concerns**:
- Add pagination support for large result sets
- Minimize API calls by batching operations where possible

## 5. Testing and Deployment

**Testing Strategy**:
- Comprehensive unit tests with mocked API responses
- Test all operations and error conditions
- Test URL extraction with various URL formats
- Test API client initialization with different library versions

**Documentation Requirements**:
- Clear README with usage examples for all operations
- Example code showing both ID and URL-based usage
- Error handling examples and token management guidance

## 6. Learned Best Practices

**Error Handling Best Practices**:
- Return errors as structured objects instead of raising exceptions
- Include detailed context in error responses for debugging
- Add safeguards against common API issues (rate limiting, auth)

**Parameter Processing Best Practices**:
- Extract IDs from user-friendly inputs like URLs
- Provide helper methods for complex parameter construction
- Include utility methods to simplify API responses

**Initialization Best Practices**:
- Use tracking flags to prevent infinite recursion
- Support multiple authentication methods
- Handle API client initialization failures gracefully
```