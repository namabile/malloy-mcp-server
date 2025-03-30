This MCP server will expose tools, resources, and prompts for working with  and analyzing data modeled using https://www.malloydata.dev/ and exposed via the malloy-publisher API (https://github.com/malloydata/publisher).

To create the server:
- Use the official Python SDK for MCP here https://github.com/modelcontextprotocol/python-sdk/blob/main/README.md
-- do not use FastAPI. use the provided link above for the offical python sdk for MCP provided by anthropic
- Use uv for dependency management, no pip or poetry
- Use the malloy python package as needed to create and validate queries


Implementation details of the Malloy MCP server:
- Use the https://pypi.org/project/molloy-publisher-client/
- Use the MCP cli and the MCP inspector as described here: https://modelcontextprotocol.io/docs/tools/inspector
- Use Pydantic models for input / output validation
- On startup create a connection to the api on localhost:4000
-- The malloy publisher will already be running
-- There are no authentication credentials required to access the malloy publisher
- Assume there is only one malloy project called "home"
- Expose the following resources to the client:
-- Metadata about the "home" project
-- The list of malloy packages available on the publisher along with their descriptions and any other package metadata
-- For each package expose the list of models that are available along with the model metadata

-- For each model, provide it's path and description and any other metadata including the malloy query syntax 
- Ignore the schedules and database components of the malloy publishers; these are not relevant to the MCP server
- The MCP server should expose the following tools:
-- Execute Malloy query: using the create malloy query prompt if needed, run a query on the malloy publisher
- The MCP server should expose the following prompts:
-- Create Malloy query: this prompt should use the malloy documentation and best practices to create help the LLM write malloy queries using the available sources and views that the publisher exposes
- The server should handle errors; when returning errors to the client, provide back a english description of the error and the context that was passed to the publisher so that the LLM can figure out how to retry its request
- Do not expose internal server errors e.g. python stack traces, etc.




