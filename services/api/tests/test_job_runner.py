import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from sqlmodel import Session, SQLModel, create_engine

from services.job_runner import (
    JobRunRecord,
    create_job_run,
    has_completed_for_date,
    has_processing_lock,
    update_job_status,
)


def test_job_run_lifecycle_and_queries() -> None:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    record = create_job_run("nightly_export", date(2026, 9, 15), engine=engine)

    assert record.status == "pending"
    assert not has_processing_lock("nightly_export", engine=engine)
    update_job_status(record.id, "processing", engine=engine)
    assert has_processing_lock("nightly_export", engine=engine)

    update_job_status(record.id, "completed", engine=engine)
    assert not has_processing_lock("nightly_export", engine=engine)
    assert has_completed_for_date("nightly_export", date(2026, 9, 15), engine=engine)

    with Session(engine) as session:
        persisted = session.get(JobRunRecord, record.id)
        assert persisted is not None
        assert persisted.started_at is not None
        assert persisted.finished_at is not None
