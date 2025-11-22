# Prompt-Driven Email Productivity Agent

A free, deployable email agent powered by local LLMs (Ollama) that helps you manage your inbox intelligently.

## Features

- **Smart Email Categorization** - Automatically categorizes emails into Important, Newsletter, Spam, or To-Do
- **Action Item Extraction** - Identifies tasks, deadlines, and requests from emails
- **AI-Powered Drafting** - Generates context-aware email replies
- **Customizable Prompts** - Full control over how the AI processes your emails
- **Chat Interface** - Natural language interaction with your email agent
- **Analytics** - Processing statistics and performance metrics
- **100% Free** - Uses local LLMs with Ollama, no API costs

## Tech Stack

- **Frontend**: Streamlit
- **AI/LLM**: Ollama + Mistral 7B (local, free)
- **Database**: In-memory with JSON persistence
- **Deployment**: Streamlit Community Cloud (free)

## Prerequisites

1. **Python 3.9+** installed
2. **Ollama** installed ([Download here](https://ollama.ai))
3. Pull the Mistral model: `ollama pull mistral:7b`

## Quick Start

### 1. Clone & Setup
```bash
# Clone or download the project
cd "Prompt-Driven Email"

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Application
```bash
streamlit run app.py
```

### 3. Access the App
Open `http://localhost:8501` in your browser.

### 4. Load Mock Inbox
On the Home page, click **"Load Mock Inbox"** to initialize 12 sample emails for testing.

## Project Structure

```
Prompt-Driven Email/
├── app.py                 # Main Streamlit application (7 pages)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── fixed/                # Clean modules (prompt-driven, persistent)
│   ├── core/             # Core processing & prompt integration
│   │   ├── email_processor.py  # Prompt-driven email processing
│   │   ├── llm_client.py       # Ollama client with heuristic fallbacks
│   │   └── prompt_manager.py   # JSON prompt loading/saving
│   ├── data/             # Data persistence layer
│   │   ├── db_manager.py       # In-memory DB with JSON persistence
│   │   └── mock_emails.py      # Mock data loader
│   ├── models/           # Pydantic data models
│   │   └── email_models.py     # Email, Draft, PromptConfig schemas
│   └── utils/            # Utilities
│       └── helpers.py          # Helper functions
├── data/                 # Data storage
│   ├── mock_emails.json        # Sample email data (12 emails)
│   └── persistent_store.json   # Saved state (auto-generated)
├── assets/prompts/       # Prompt templates
│   ├── default_prompts.json    # 10 default prompts
│   └── custom_prompts.json     # User-editable custom prompts
└── tests/                # Automated tests
    └── smoke_test.py           # Feature validation suite
```

## How to Use

### Processing Emails (AI Tools Page)
1. Navigate to **"AI Tools"** page
2. Select an email ID or use batch process
3. Choose processing action:
   - **Categorize**: Assigns category, urgency, confidence
   - **Extract Actions**: Identifies tasks and deadlines
   - **Summarize**: Generates key points summary
   - **Draft Reply**: Creates context-aware reply with selected tone
4. Processing logs captured (view in Analytics → Recent Logs)

### Customizing Prompts (Prompt Brain Page)
1. Go to **"Prompt Brain"** page
2. Select a prompt to view/edit
3. Modify the prompt text
4. Save your custom version (written to `assets/prompts/custom_prompts.json`)
5. Edits persist across restarts (JSON storage)

### Managing Drafts (Drafts Page)
1. Navigate to **"Drafts"** page
2. View all generated and manual drafts
3. Edit draft content, subject, or recipients
4. Mark drafts as sent (safe, no actual sending)
5. Create new manual drafts with full metadata

### Chat with Email Agent (Chat Page)
1. Go to **"Chat"** page
2. Select emails for context
3. Use Quick Query presets or type custom questions:
   - "Summarize selected emails"
   - "Show urgent emails"
   - "Draft reply for selected (tone professional)"
4. Responses generated using current prompt definitions

### Analytics Dashboard (Analytics Page)
Open **"Analytics"** to view:
- Total, processed, urgent (heuristic) email counts
- Category distribution pie chart
- Aggregated action items table
- Recent processing logs with durations

## Data Persistence

All application state is automatically saved to `data/persistent_store.json`:
- **Emails**: Inbox items with processing status
- **Drafts**: Generated and manual drafts with metadata
- **Prompts**: Custom prompt configurations
- **Logs**: Processing history with timestamps

Persistence is automatic—restart the app to verify state restoration.

## Configuration

### Environment Variables (Optional)
Create a `.env` file for custom configuration:
```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral:7b
APP_ENV=development
```

### Supported LLM Models
- `mistral:7b` (Recommended - free, local)
- `llama2:7b` (Alternative)
- `gemma:7b` (Alternative)

**Note**: The app includes deterministic heuristic fallbacks, so it works offline without Ollama.

## Troubleshooting

### Module Import Errors / Corrupted Source
If you encounter `SyntaxError: source code string cannot contain null bytes`:
- The project uses clean `fixed/` modules
- Ensure imports reference `fixed.*` packages
- Delete any corrupted original files if present

### Ollama Connection Issues
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Pull the model if missing
ollama pull mistral:7b
```

### Port Already in Use
```bash
# Use different port
streamlit run app.py --server.port=8502
```

### Data Persistence Issues
- Check `data/persistent_store.json` exists and is valid JSON
- Delete the file to reset state if corrupted
- Run the smoke test: `python tests/smoke_test.py`

## Testing

### Automated Smoke Tests
Run the comprehensive test suite to validate all features:
```bash
python tests/smoke_test.py
```

**Tests cover:**
- Mock email ingestion (12 emails)
- Email categorization (prompt-driven)
- Action item extraction
- Email summarization
- Auto-reply draft generation
- Custom prompt saving/loading
- JSON persistence integrity

### Manual Testing Checklist
1. Load mock inbox → Verify 12 emails appear
2. Process an email → Check categorization/actions/summary
3. Edit a prompt → Save and reload to confirm persistence
4. Generate a draft → Verify it appears in Drafts page
5. Restart app → Confirm all data restored from JSON

### Local Production
```bash
# Set production environment
$env:APP_ENV="production"  # PowerShell
# or: export APP_ENV=production  # Unix/Linux

# Run with custom settings
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

## Performance & Best Practices
- **Batch Processing**: Process multiple emails at once in AI Tools page
- **Prompt Optimization**: Customize prompts for your specific use case
- **Offline Mode**: App works with heuristic fallbacks when Ollama unavailable
- **Error Handling**: Graceful degradation on LLM failures

## Safety Features
- **No Auto-Sending**: All drafts require manual review
- **Local Processing**: Your data never leaves your machine (with local Ollama)
- **Content Validation**: Input sanitization and Pydantic validation
- **Error Handling**: Multi-encoding support and graceful fallbacks
