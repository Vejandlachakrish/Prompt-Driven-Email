# -*- coding: utf-8 -*-
import streamlit as st

# Ensure page config set exactly once and as the first Streamlit command
if "_page_config_set" not in st.session_state:
    st.set_page_config(page_title="Email Productivity Agent", page_icon="📧", layout="wide")
    st.session_state["_page_config_set"] = True

import os
from datetime import datetime
import pandas as pd

"""Application entry uses clean fixed modules after original corruption."""
from fixed.data import db_manager
from fixed.data.mock_emails import initialize_mock_data  # use clean mock loader
from fixed.core.email_processor import EmailProcessor
from fixed.core.prompt_manager import PromptManager
from fixed.models.email_models import DraftCreate, PromptConfigCreate

import ollama

# Environment defaults
os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")
os.environ.setdefault("OLLAMA_MODEL", "mistral:7b")

st.title("📧 Email Productivity Agent")

# Session state initialization
if "emails_loaded" not in st.session_state:
    st.session_state.emails_loaded = False
if "selected_email_id" not in st.session_state:
    st.session_state.selected_email_id = None
if "processing_results" not in st.session_state:
    st.session_state.processing_results = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

prompt_mgr = PromptManager()
processor = EmailProcessor(prompt_mgr)

# Status metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Status", "Online")
with col2:
    try:
        client = ollama.Client(host=os.environ["OLLAMA_HOST"])
        _models = client.list()
        st.metric("Ollama", "Connected")
    except Exception:
        st.metric("Ollama", "Error")
with col3:
    st.metric("Emails", str(len(db_manager.get_all_emails())))
with col4:
    st.metric("Drafts", str(len(db_manager.get_all_drafts())))

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Home", "Inbox", "AI Tools", "Prompt Brain", "Drafts", "Chat", "Analytics"]
)

# Sidebar actions
st.sidebar.subheader("Actions")
if st.sidebar.button("Load Mock Inbox", disabled=st.session_state.emails_loaded):
    added = initialize_mock_data(db_manager)
    st.session_state.emails_loaded = True if added > 0 else False
    st.sidebar.success(f"Loaded {added} emails")

if st.sidebar.button("Refresh"):
    st.rerun()

# Helper to fetch emails (convert to display dict)
def fetch_emails():
    results = []
    for e in db_manager.get_all_emails(limit=500):
        # Urgency heuristic
        body_lower = (e.body or '').lower()
        urgent = any(k in body_lower for k in ["urgent", "asap", "priority", "critical"]) or (e.action_items and len(e.action_items) > 0)
        results.append({
            "id": e.id,
            "sender": e.sender,
            "subject": e.subject,
            "date": e.date.strftime("%Y-%m-%d %H:%M"),
            "category": e.category,
            "processed": e.is_processed,
            "urgent": urgent
        })
    return results

def get_email_by_id(eid):
    return db_manager.get_email(eid)

def map_email_for_llm(email):
    return {
        "from": email.sender,
        "to": email.recipient,
        "subject": email.subject,
        "body": email.body,
        "date": email.date.isoformat() if email.date else ""
    }

def log_operation(email_id:int, operation:str, status:str, input_payload:dict, output_payload:dict, start_time:datetime):
    duration = (datetime.utcnow() - start_time).total_seconds()
    db_manager.add_processing_log({
        "email_id": email_id,
        "operation": operation,
        "status": status,
        "input_data": input_payload,
        "output_data": output_payload,
        "error_message": None if status=="success" else output_payload.get("error"),
        "processing_time": duration,
        "llm_model": os.environ.get("OLLAMA_MODEL", "mistral:7b")
    })

def apply_processing(email_obj, operations, tone: str = "professional"):
    email_dict = map_email_for_llm(email_obj)
    results = {}
    for op in operations:
        start = datetime.utcnow()
        if op == "categorization":
            cat = processor.process_email_categorization(email_dict)
            results.update({"category": cat["category"],"category_confidence": cat["confidence"],"category_reason": cat["reason"]})
            log_operation(email_obj.id, op, "success", email_dict, cat, start)
        elif op == "action_extraction":
            act = processor.process_action_extraction(email_dict)
            # Normalize tasks into list of strings
            tasks_raw = act.get("tasks", [])
            if isinstance(tasks_raw, list):
                tasks_norm = []
                for t in tasks_raw:
                    if isinstance(t, dict):
                        tasks_norm.append(t.get("task") or str(t))
                    else:
                        tasks_norm.append(str(t))
            else:
                tasks_norm = [str(tasks_raw)]
            results.update({"action_items": tasks_norm})
            log_operation(email_obj.id, op, "success", email_dict, act, start)
        elif op == "summarization":
            summ = processor.summarize_email(email_dict)
            results.update({"summary": summ.get("summary", [])})
            log_operation(email_obj.id, op, "success", email_dict, summ, start)
    if results:
        db_manager.update_email_processing(email_obj.id, results)
    return results

def generate_reply(email_obj, tone: str):
    data = map_email_for_llm(email_obj)
    # Inject tone into prompt by temporarily replacing placeholder
    prompt_template = prompt_mgr.get_prompt('auto_reply')
    if "{tone}" in prompt_template:
        prompt_text = prompt_template.replace("{tone}", tone)
    else:
        prompt_text = prompt_template + f"\nTone: {tone}"
    # Build pseudo email_data for client
    full_prompt = prompt_text.format(email_content=processor._format_email_content(data))
    structured = processor.llm_client.generate_json_response(full_prompt)
    reply = {
        "subject": structured.get("subject", f"Re: {email_obj.subject}"),
        "body": structured.get("body", ""),
        "tone": structured.get("tone", tone),
        "follow_ups": structured.get("follow_ups", [])
    }
    draft = DraftCreate(
        subject=reply["subject"],
        body=reply["body"],
        recipient=email_obj.sender,
        tone=reply.get("tone", tone),
        original_email_id=email_obj.id,
        generated_by_ai=True
    )
    db_manager.add_draft(draft)
    log_operation(email_obj.id, "auto_reply", "success", data, reply, datetime.utcnow())
    return reply

# Pages
if page == "Home":
    st.header("Welcome")
    st.write("Use the sidebar to load mock emails and explore AI tools.")
    st.info("Next: Load mock inbox, open 'Inbox' to process.")

elif page == "Inbox":
    st.header("Inbox")
    emails = fetch_emails()
    if not emails:
        st.warning("No emails loaded yet. Use 'Load Mock Inbox' in sidebar.")
    else:
        st.subheader("Email List")
        df = pd.DataFrame(emails)
        # Styled HTML table with badges/icons
        category_colors = {
            "Important": "#d9534f",
            "To-Do": "#f0ad4e",
            "Newsletter": "#5bc0de",
            "Spam": "#6c757d",
            "Uncategorized": "#999999"
        }
        def badge(cat):
            color = category_colors.get(cat, "#777")
            return f"<span style='background:{color};color:#fff;padding:2px 6px;border-radius:12px;font-size:12px;'>{cat}</span>"
        def icon_bool(val):
            return "✅" if val else "❌"
        def urgent_icon(val):
            return "⚠️" if val else ""
        rows_html = []
        rows_html.append("<tr><th>ID</th><th>Sender</th><th>Subject</th><th>Date</th><th>Category</th><th>Processed</th><th>Urgent</th></tr>")
        for _, r in df.sort_values("date", ascending=False).iterrows():
            rows_html.append(
                f"<tr>" 
                f"<td>{r.id}</td>" 
                f"<td>{r.sender}</td>" 
                f"<td>{r.subject}</td>" 
                f"<td>{r.date}</td>" 
                f"<td>{badge(r.category)}</td>" 
                f"<td>{icon_bool(r.processed)}</td>" 
                f"<td>{urgent_icon(r.urgent)}</td>" 
                f"</tr>"
            )
        table_html = "<table style='width:100%;border-collapse:collapse;'>" + "".join(rows_html) + "</table>"
        st.markdown(table_html, unsafe_allow_html=True)
        selected = st.number_input("Select Email ID", min_value=int(df.id.min()), max_value=int(df.id.max()), step=1, value=int(df.id.min()))
        st.session_state.selected_email_id = selected
        email_obj = get_email_by_id(int(selected))
        tone_choice = st.selectbox("Reply Tone", ["professional","friendly","formal","concise"], index=0)
        if st.button("Process Selected: Categorize+Actions+Summarize"):
            res = apply_processing(email_obj, ["categorization","action_extraction","summarization"], tone=tone_choice)
            st.session_state.processing_results[email_obj.id] = res
            st.success("Email fully processed.")
        if st.button("Draft Reply with Tone"):
            reply = generate_reply(email_obj, tone_choice)
            st.session_state.processing_results[email_obj.id] = {**st.session_state.processing_results.get(email_obj.id, {}), "draft": reply}
            st.success("Reply draft generated.")
        if st.button("Process All Unprocessed"):
            for row in df.to_dict("records"):
                eobj = get_email_by_id(row['id'])
                if eobj and not eobj.is_processed:
                    apply_processing(eobj,["categorization","action_extraction"], tone=tone_choice)
            st.success("Batch categorization + action extraction complete.")
        with st.expander("Selected Email Details", expanded=True):
            st.markdown(f"**From:** {email_obj.sender}")
            st.markdown(f"**Subject:** {email_obj.subject}")
            st.markdown(f"**Date:** {email_obj.date}")
            st.markdown(f"**Category:** {email_obj.category}")
            st.code(email_obj.body, language="text")
        if email_obj.id in st.session_state.processing_results:
            st.subheader("Results")
            r = st.session_state.processing_results[email_obj.id]
            if "category" in r:
                st.write(f"Category: **{r['category']}** (conf: {r.get('category_confidence',0):.2f})")
                st.caption(r.get("category_reason", ""))
            if "action_items" in r:
                st.write("Action Items:")
                for t in r["action_items"]:
                    st.write(f"- {t}")
            if "summary" in r:
                st.write("Summary:")
                for s in r["summary"]:
                    st.write(f"• {s}")
            if "draft" in r:
                st.write("Draft Reply:")
                st.markdown(f"**Subject:** {r['draft']['subject']}")
                st.code(r['draft']['body'])
                if r['draft'].get('follow_ups'):
                    st.write("Suggested Follow-Ups:")
                    for f in r['draft']['follow_ups']:
                        st.write(f"• {f}")

elif page == "AI Tools":
    st.header("Batch Processing")
    emails = fetch_emails()
    if not emails:
        st.warning("Load inbox first.")
    else:
        selected_ids = st.multiselect("Select Emails", options=[e["id"] for e in emails])
        ops = st.multiselect("Operations", ["categorization", "action_extraction", "summarization"])
        if st.button("Run Batch") and selected_ids and ops:
            for eid in selected_ids:
                email_obj = get_email_by_id(eid)
                if email_obj:
                    res = apply_processing(email_obj, ops)
                    st.session_state.processing_results[email_obj.id] = {
                        **st.session_state.processing_results.get(email_obj.id, {}), **res}
            st.success("Batch processing complete.")
        st.write("Processed Results Preview:")
        for eid, data in st.session_state.processing_results.items():
            st.write(f"Email {eid}: {list(data.keys())}")

elif page == "Prompt Brain":
    st.header("Prompt Brain")
    all_prompts = prompt_mgr.get_all_prompts()
    st.subheader("Default & Custom Prompts")
    for key, meta in all_prompts.items():
        with st.expander(meta.get("name", key)):
            st.write(meta.get("description", ""))
            st.code(meta.get("prompt", ""), language="text")
    st.divider()
    st.subheader("Create / Update Custom Prompt")
    p_type = st.selectbox("Prompt Type", ["categorization", "action_extraction", "auto_reply", "summarization", "custom"])
    p_name = st.text_input("Name", value=f"Custom {p_type.title()}")
    p_desc = st.text_area("Description", value="Custom prompt for experimentation")
    p_text = st.text_area("Prompt Text", height=180)
    if st.button("Save Custom Prompt"):
        prompt_mgr.save_custom_prompt(p_type, p_text, name=p_name, description=p_desc)
        # store in DB prompt configs
        db_manager.add_prompt_config(PromptConfigCreate(
            name=p_name,
            prompt_type=p_type,
            prompt_text=p_text,
            description=p_desc,
            is_custom=True,
            is_active=True
        ))
        st.success("Custom prompt saved.")
        st.rerun()

elif page == "Drafts":
    st.header("Drafts")
    st.subheader("Create New Draft")
    with st.form("new_draft_form"):
        nd_recipient = st.text_input("Recipient", value="example@domain.com")
        nd_subject = st.text_input("Subject", value="Status Update")
        nd_body = st.text_area("Body", height=160, value="Hello,\n\nHere is the requested update...\n\nRegards,")
        nd_tone = st.selectbox("Tone", ["professional","friendly","formal","concise"], index=0)
        attach_email_id = st.number_input("Link to Email ID (optional)", min_value=0, step=1, value=0)
        submitted = st.form_submit_button("Create Draft")
        if submitted:
            linked_email = db_manager.get_email(int(attach_email_id)) if attach_email_id > 0 else None
            draft = DraftCreate(
                subject=nd_subject,
                body=nd_body,
                recipient=nd_recipient,
                tone=nd_tone,
                original_email_id=linked_email.id if linked_email else None,
                generated_by_ai=False,
                category=getattr(linked_email, 'category', None),
                action_items=getattr(linked_email, 'action_items', None)
            )
            db_manager.add_draft(draft)
            st.success("Draft created.")
            st.rerun()
    st.divider()
    drafts = db_manager.get_all_drafts()
    if not drafts:
        st.info("No drafts yet. Generate or create one above.")
    else:
        draft_ids = [d.id for d in drafts]
        selected = st.selectbox("Select Draft", draft_ids)
        draft_obj = next(d for d in drafts if d.id == selected)
        st.text_input("Subject", value=draft_obj.subject, key="draft_subject")
        new_body = st.text_area("Body", value=draft_obj.body, height=200, key="draft_body")
        if st.button("Save Changes"):
            db_manager.update_draft(draft_obj.id, {"subject": st.session_state.draft_subject, "body": new_body})
            st.success("Draft updated.")
            st.experimental_rerun()
        meta_parts = []
        if getattr(draft_obj, 'category', None):
            meta_parts.append(f"Category: {draft_obj.category}")
        if getattr(draft_obj, 'action_items', None):
            meta_parts.append(f"Actions: {len(draft_obj.action_items)}")
        st.caption(f"Tone: {draft_obj.tone} | AI: {'Yes' if draft_obj.generated_by_ai else 'No'} | " + " | ".join(meta_parts))

elif page == "Chat":
    st.header("Email Agent Chat")
    emails = fetch_emails()
    multi_context = st.multiselect("Context Emails (optional)", [f"#{e['id']} {e['subject']}" for e in emails])
    preset = st.selectbox("Quick Query", ["None","Summarize selected emails","List all action items","Show urgent emails","Draft reply for selected (tone professional)"])    
    user_msg = st.text_input("Custom Question")
    send_trigger = st.button("Send")
    if send_trigger:
        context_blocks = []
        for c in multi_context:
            eid = int(c.split()[0].replace('#',''))
            eobj = get_email_by_id(eid)
            if eobj:
                context_blocks.append(f"EMAIL #{eid}\nSubject: {eobj.subject}\nBody: {eobj.body}\nCategory: {eobj.category}\n")
        context_text = "\n---\n".join(context_blocks)
        query = user_msg if preset=="None" else preset
        composed = f"You are an email productivity agent.\nContext Emails:\n{context_text}\nUser Query: {query}\nRespond clearly."
        answer = processor.llm_client.generate_response(composed)
        st.session_state.chat_history.append({"role":"user","content":query,"time":datetime.utcnow()})
        st.session_state.chat_history.append({"role":"assistant","content":answer,"time":datetime.utcnow()})
    for msg in reversed(st.session_state.chat_history[-50:]):
        st.markdown(f"**{msg['role'].title()}** ({msg['time'].strftime('%H:%M:%S')}): {msg['content']}")

elif page == "Analytics":
    st.header("Analytics & Metrics")
    emails = fetch_emails()
    if not emails:
        st.info("Load emails first.")
    else:
        import pandas as pd
        df = pd.DataFrame(emails)
        total = len(df)
        processed = df[df.processed].shape[0]
        cat_counts = df.groupby('category').size().to_dict()
        urgent_count = df[df.urgent].shape[0]
        st.metric("Total Emails", total)
        st.metric("Processed", processed)
        st.metric("Urgent (Heuristic)", urgent_count)
        st.subheader("By Category")
        for c, count in cat_counts.items():
            st.write(f"{c}: {count}")
        # Action items aggregation
        action_board = []
        for e in db_manager.get_all_emails():
            if e.action_items:
                for item in e.action_items:
                    action_board.append({"email_id": e.id, "task": item, "category": e.category})
        st.subheader("Aggregated Action Items")
        if action_board:
            st.table(pd.DataFrame(action_board))
        else:
            st.write("No action items extracted yet.")
        st.subheader("Recent Processing Logs")
        logs = db_manager.get_processing_logs(limit=25)
        if logs:
            log_rows = []
            for l in logs:
                log_rows.append({"email_id": l.email_id, "operation": l.operation, "status": l.status, "time": l.processing_time, "created": l.created_at})
            st.dataframe(pd.DataFrame(log_rows), use_container_width=True)
        else:
            st.write("No logs yet.")

