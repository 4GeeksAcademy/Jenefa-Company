@JeneJohn ➜ /workspaces/Jenefa-Company/services/api (feature/websocket-chat) $ uvicorn app.main:app --reload --port 8000
INFO:     Will watch for changes in these directories: ['/workspaces/Jenefa-Company/services/api']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [27394] using WatchFiles
22:33:29.705 | ERROR   | services.langgraph_agent.websocket - WebSocket agent generation failed
Traceback (most recent call last):
  File "/workspaces/Jenefa-Company/services/langgraph_agent/websocket.py", line 57, in _stream_answer
    state = await asyncio.to_thread(
            ^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
    )
    ^
  File "/usr/local/python/3.14.2/lib/python3.14/asyncio/threads.py", line 25, in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/python/3.14.2/lib/python3.14/concurrent/futures/thread.py", line 86, in run
    result = ctx.run(self.task)
  File "/usr/local/python/3.14.2/lib/python3.14/concurrent/futures/thread.py", line 73, in run
    return fn(*args, **kwargs)
  File "/workspaces/Jenefa-Company/services/langgraph_agent/guardrails.py", line 147, in guarded_invoke_agent
    state = invoke_agent(
        normalized,
    ...<3 lines>...
        memory_store=memory_store,
    )
  File "/workspaces/Jenefa-Company/services/langgraph_agent/graph.py", line 208, in invoke_agent
    return graph.invoke(
           ~~~~~~~~~~~~^
        {
        ^
    ...<12 lines>...
        config=run_config,
        ^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/langgraph/pregel/main.py", line 3913, in invoke
    for chunk in self.stream(
                 ~~~~~~~~~~~^
        input,
        ^^^^^^
    ...<11 lines>...
        **kwargs,
        ^^^^^^^^^
    ):
    ^
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/langgraph/pregel/main.py", line 2967, in stream
    for _ in runner.tick(
             ~~~~~~~~~~~^
        [t for t in loop.tasks.values() if not t.writes],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<2 lines>...
        schedule_task=loop.accept_push,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/langgraph/pregel/_runner.py", line 207, in tick
    run_with_retry(
    ~~~~~~~~~~~~~~^
        t,
        ^^
    ...<10 lines>...
        },
        ^^
    )
    ^
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/langgraph/pregel/_retry.py", line 617, in run_with_retry
    return task.proc.invoke(task.input, config)
           ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/langgraph/_internal/_runnable.py", line 707, in invoke
    input = context.run(step.invoke, input, config, **kwargs)
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/langgraph/_internal/_runnable.py", line 447, in invoke
    ret = self.func(*args, **kwargs)
  File "/workspaces/Jenefa-Company/services/langgraph_agent/graph.py", line 172, in <lambda>
    graph.add_node("retrieve", lambda state: retrieve_node(state, retriever=retriever, trace_callback=trace_callback))
                                             ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/workspaces/Jenefa-Company/services/langgraph_agent/graph.py", line 75, in retrieve_node
    chunks = retriever(state["question"])
  File "/workspaces/Jenefa-Company/services/langgraph_agent/guardrails.py", line 138, in isolated_retriever
    chunks = base_retriever(request)
  File "/workspaces/Jenefa-Company/data/pipelines/rag.py", line 26, in retrieve
    qdrant = client or _client()
                       ~~~~~~~^^
  File "/workspaces/Jenefa-Company/data/pipelines/rag.py", line 21, in _client
    return QdrantClient(url=url, api_key=os.getenv("QDRANT_API_KEY"))
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/qdrant_client/qdrant_client.py", line 134, in __init__
    self._client = QdrantRemote(
                   ~~~~~~~~~~~~^
        url=url,
        ^^^^^^^^
    ...<13 lines>...
        **kwargs,
        ^^^^^^^^^
    )
    ^
  File "/usr/local/python/3.14.2/lib/python3.14/site-packages/qdrant_client/qdrant_remote.py", line 118, in __init__
    raise ValueError(f"Unknown scheme: {self._scheme}")
ValueError: Unknown scheme: sqlite
During task with name 'retrieve' and id 'bcf5a92f-3b01-c042-9703-b3fecd2daecd'
