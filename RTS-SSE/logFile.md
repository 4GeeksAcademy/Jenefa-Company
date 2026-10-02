@JeneJohn ➜ /workspaces/Jenefa-Company (feature/owasp-top10-audit) $ HEALTHCORE_MCP_URL="http://mcp.test" HEALTHCORE_SERVICE_TOKEN="mock-audit-token-123" python -m pytest services/api/tests/test_mcp_oauth_tools.py
====================== test session starts =======================
platform linux -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
rootdir: /workspaces/Jenefa-Company/services/api
configfile: pyproject.toml
plugins: anyio-4.15.1, langsmith-0.14.2
collected 1 item                                                 

services/api/tests/test_mcp_oauth_tools.py F               [100%]

============================ FAILURES ============================
______________ test_mcp_connections_adapter_schema _______________

    def test_mcp_connections_adapter_schema():
        """
        Test 48: Confirm that the LangGraph adapter connection mapping layer
        correctly reads environment variables and constructs a valid schema.
        """
        # Execute the connection mapping contract check
        config = mcp_connections()
    
        assert "healthcore" in config
        assert config["healthcore"]["transport"] == "http"
>       assert config["healthcore"]["url"].endswith("/mcp")
E       AssertionError: assert False
E        +  where False = <built-in method endswith of str objectat 0x7de0b11ba8b0>('/mcp')
E        +    where <built-in method endswith of str object at 0x7de0b11ba8b0> = 'http://mcp.test'.endswith

services/api/tests/test_mcp_oauth_tools.py:14: AssertionError
==================== short test summary info =====================
FAILED services/api/tests/test_mcp_oauth_tools.py::test_mcp_connections_adapter_schema - AssertionError: assert False
======================= 1 failed in 1.40s ========================
@JeneJohn ➜ /workspaces/Jenefa-Company (feature/owasp-top10-audit) $ 