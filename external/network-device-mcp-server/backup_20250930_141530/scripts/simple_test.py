import sys
print("Python version:", sys.version)
print("Python executable:", sys.executable)

try:
    import mcp
    print("MCP import: SUCCESS")
except Exception as e:
    print("MCP import: FAILED -", str(e))

try:
    from mcp.server import Server
    print("MCP Server import: SUCCESS")
except Exception as e:
    print("MCP Server import: FAILED -", str(e))

print("Test complete")
