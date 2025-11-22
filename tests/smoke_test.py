"""Automated smoke test for Prompt-Driven Email Productivity Agent.

Run:
  python tests/smoke_test.py

Ensures core functionalities work: ingestion, categorization, action extraction,
summarization, auto-reply draft creation, persistence, and prompt customization.
"""
from pathlib import Path
import json
import time
import sys
import pathlib

# Ensure project root (parent of tests/) is on sys.path so 'fixed' package resolves
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fixed.data import db_manager  # type: ignore
from fixed.data.mock_emails import initialize_mock_data  # type: ignore
from fixed.core.prompt_manager import PromptManager  # type: ignore
from fixed.core.email_processor import EmailProcessor  # type: ignore
from fixed.models.email_models import DraftCreate  # type: ignore


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"[OK] {message}")


def test_ingestion():
    before = len(db_manager.get_all_emails())
    added = initialize_mock_data(db_manager)
    after = len(db_manager.get_all_emails())
    assert_true(added > 0, "Mock emails added")
    assert_true(after >= before + added, "Email count increased after ingestion")


def test_processing():
    pm = PromptManager()
    processor = EmailProcessor(pm)
    emails = db_manager.get_all_emails()
    assert_true(len(emails) > 0, "Emails available for processing")
    e = emails[0]
    email_dict = {
        "from": e.sender,
        "to": e.recipient,
        "subject": e.subject,
        "body": e.body,
        "date": e.date.isoformat(),
    }
    cat = processor.process_email_categorization(email_dict)
    assert_true("category" in cat, "Categorization returned a category")
    actions = processor.process_action_extraction(email_dict)
    assert_true("tasks" in actions, "Action extraction returned tasks list")
    summ = processor.summarize_email(email_dict)
    assert_true("summary_points" in summ, "Summarization returned points")


def test_auto_reply_and_draft():
    pm = PromptManager()
    processor = EmailProcessor(pm)
    e = db_manager.get_all_emails()[0]
    email_dict = {
        "from": e.sender,
        "to": e.recipient,
        "subject": e.subject,
        "body": e.body,
        "date": e.date.isoformat(),
    }
    prompt_template = pm.get_prompt("auto_reply")
    full_prompt = prompt_template.replace("{tone}", "professional").replace("{email_content}", processor._format_email_content(email_dict))
    reply = processor.llm_client.generate_json_response(full_prompt)
    assert_true("body" in reply and "subject" in reply, "Auto-reply generated subject and body")
    draft = DraftCreate(
        subject=reply["subject"],
        body=reply["body"],
        recipient=e.sender,
        tone=reply.get("tone", "professional"),
        original_email_id=e.id,
        generated_by_ai=True,
        category=getattr(e, "category", None),
        action_items=getattr(e, "action_items", None)
    )
    db_manager.add_draft(draft)
    assert_true(len(db_manager.get_all_drafts()) > 0, "Draft stored in persistence layer")


def test_prompt_customization():
    pm = PromptManager()
    custom_key = "categorization_custom_test"
    pm.save_custom_prompt(custom_key, "Test prompt with {tone} and {email_content}")
    all_prompts = pm.get_all_prompts()
    assert_true(custom_key in all_prompts, "Custom prompt saved and loaded")


def test_persistence_file():
    # Resolve project root data directory regardless of CWD
    store_path = ROOT / "data" / "persistent_store.json"
    if not store_path.exists():
        # Force a save in case previous mutations did not flush yet
        try:
            db_manager._save_state()  # type: ignore
        except Exception:
            pass
    assert_true(store_path.exists(), "persistent_store.json created")
    data = json.loads(store_path.read_text(encoding="utf-8"))
    assert_true("emails" in data and isinstance(data["emails"], list), "Emails persisted to JSON store")
    assert_true("drafts" in data and isinstance(data["drafts"], list), "Drafts persisted to JSON store")


def run_all():
    print("Running smoke tests...")
    test_ingestion()
    test_processing()
    test_auto_reply_and_draft()
    test_prompt_customization()
    # Allow save to flush
    time.sleep(0.2)
    test_persistence_file()
    print("All smoke tests passed successfully.")


if __name__ == "__main__":
    run_all()