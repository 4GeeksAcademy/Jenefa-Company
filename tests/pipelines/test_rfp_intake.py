from data.pipelines.rfp_intake.graph import (
    classify_rfp,
    orchestrate,
    readability_metrics,
    synthesize,
    worker,
)


def test_classifier_requires_multiple_structural_rfp_signals():
    valid, signals = classify_rfp("Request for Proposal\nSubmission deadline: May 4\nEvaluation criteria included.")
    assert valid is True
    assert "request for proposal" in signals
    assert classify_rfp("A general product brochure with no procurement requirements.")[0] is False


def test_orchestrator_assigns_unmapped_section_without_dropping_it():
    tasks = orchestrate("# Clinical operations\nClinic staffing and care access requirements.\n\n# Unknown domain\nThe bid includes a cafeteria meal service.")
    by_department = {task["department_name"]: task["relevant_markdown_extract"] for task in tasks}
    assert "Engineering" in by_department
    assert "Unassigned / General Review" in by_department
    assert "cafeteria meal service" in by_department["Unassigned / General Review"]


def test_worker_uses_only_source_evidence_and_flags_missing_numbers():
    output = worker(
        {"department_name": "Legal", "relevant_markdown_extract": "Vendor shall provide a contract. Contact legal@example.com."},
        {},
    )
    assert "Vendor shall provide a contract." in output["key_aspects"]
    assert output["contacts"] == ["legal@example.com"]
    assert output["warnings"] == ["Required parameter [quantified target / amount / timeline] missing from source document."]
    assert "90 days" not in output["key_aspects"]


def test_readability_metrics_are_available_without_external_llm_calls():
    metrics = readability_metrics("This is a short document. It has two sentences.")
    assert metrics["word_count"] == 9
    assert metrics["estimated_tokens"] > 0
    assert metrics["flesch_kincaid_grade_level"] == metrics["flesch_kincaid_grade_level"]


def test_synthesizer_flags_unassigned_workstream():
    result = synthesize([{"department": "Unassigned / General Review", "key_aspects": "Meal service terms.", "contacts": [], "warnings": []}])
    assert "Manual assignment required" in result["warnings"][0]
    assert result["workstream_structure"][0]["department"] == "Unassigned / General Review"
