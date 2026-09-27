import pytest
from services.langgraph_agent.tools import mcp_connections

def test_mcp_connections_adapter_schema():
    """
    Test 48: Confirm that the LangGraph adapter connection mapping layer
    correctly reads environment variables and constructs a valid schema.
    """
    # Execute the connection mapping contract check
    config = mcp_connections()
    
    assert "healthcore" in config
    assert config["healthcore"]["transport"] == "http"
    assert config["healthcore"]["url"].endswith("/mcp")
    assert "Authorization" in config["healthcore"]["headers"]
