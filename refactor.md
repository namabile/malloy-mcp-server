# Refactoring Plan for Malloy MCP Server

This document outlines the key areas for improvement in the current implementation of the Malloy MCP Server to make it more streamlined, less verbose, and better aligned with best practices from the MCP and Malloy Publisher ecosystems.

## Issues Identified

1. **Type Inconsistencies**: The code is experiencing linting errors due to inconsistencies in type handling, particularly with `CompiledModel` from the malloy_publisher_client package.

2. **Verbose Implementation**: The current implementation uses closures and nested error handling that makes the code harder to follow than necessary.

3. **Resource Duplication**: The project defines custom resource models that could be streamlined by better utilizing the models provided by malloy_publisher_client.

4. **Over-complex Retry Logic**: The connection initialization uses manually implemented retry logic that could be simplified.

5. **Missing Implementation Details**: Some core functionality (query creation and execution) is only partially implemented with placeholder code.

## Refactoring Steps

### 1. Fix Type Handling and Model Usage

- **Import problem fix**: Replace `CompiledModel` import from `malloy_publisher_client` with the correct `Model` class and handle any necessary type adaptations.

- **Model simplification**: Use the existing Pydantic models from malloy_publisher_client directly rather than recreating them, particularly:
  - Use `Package`, `Model`, and `Project` directly
  - Remove `MalloyPackageMetadata`, `MalloyModelMetadata`, and `MalloyProjectMetadata` classes in favor of the client library versions

### 2. Streamline Resource Registration

- **Simplify resource registration**: Replace the closure-based approach with direct function decorators that use the existing models

- **Use type annotations properly**: Ensure all resource handlers have proper return type annotations that align with the client library models

- **Remove redundant model dump calls**: Instead of using `model.model_dump()`, use `model` directly or proper serialization methods

### 3. Restructure App Lifecycle Management

- **Simplify connection retry logic**: Use a more concise approach for connecting to the Malloy publisher, potentially using async helpers like `asyncio.retry` or similar patterns

- **Clean exception handling**: Make error handling more consistent throughout the application

- **Organize resource registration**: Group resource registration code more logically to improve readability

### 4. Implement Missing Functionality

- **Query execution**: Complete the implementation of the `execute_malloy_query` tool to properly handle query execution

- **Query creation prompt**: Enhance the query creation prompt to provide useful guidance based on actual Malloy model structures

### 5. Leverage MCP Types

- **Use MCP SDK Types**: Utilize the `mcp.types` module for proper typing of MCP-specific concepts

- **Resource contents typing**: Ensure resource contents are typed correctly according to the MCP specification

### 6. Code Organization

- **Module structure**: Review and potentially reorganize the module structure for better separation of concerns:
  - Keep core server initialization in `server.py`
  - Move resource handlers to an appropriate module
  - Ensure tools and prompts are organized logically

### 7. Error Handling Improvement

- **User-friendly errors**: Ensure all errors returned to the client are human-readable and don't expose implementation details

- **Context inclusion**: Include relevant context in error messages to help diagnose issues

- **Consistent patterns**: Use consistent error handling patterns throughout the codebase

## Implementation Plan

1. **Fix Import and Type Issues**:
   - Correct the imports from malloy_publisher_client
   - Fix any related type annotations

2. **Streamline Resource Definitions**:
   - Refactor resource registration to use malloy_publisher_client models directly
   - Remove redundant model definitions

3. **Simplify App Lifespan Code**:
   - Rewrite the app_lifespan function to be more concise
   - Improve error handling patterns

4. **Complete Tool and Prompt Implementations**:
   - Finish implementing the execute_malloy_query tool
   - Enhance the create_malloy_query prompt

5. **Update Tests**:
   - If tests exist, update them to match the new implementations
   - If not, consider adding tests for key functionality

6. **Documentation Updates**:
   - Update docstrings and other documentation to reflect changes
   - Ensure all public interfaces are well-documented

By following this plan, the Malloy MCP Server will be more maintainable, better aligned with the libraries it depends on, and more robust in handling errors and edge cases. 