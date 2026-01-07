@echo off
REM Network Device MCP Server Runner
call "C:\Users\keith.ransom\network-device-mcp-server\venv\Scripts\activate.bat"
python "C:\Users\keith.ransom\network-device-mcp-server\src\main.py" %*
