services/
  api/
    main.py           ← FastAPI application
    models.py         ← Pydantic models
    database.py       ← TinyDB initialisation
    routes/
      suppliers.py    ← supplier directory endpoints
    seed.py           ← initial data loading script
uis/
  backoffice/
    app/
      suppliers/      ← supplier directory page (Home)
