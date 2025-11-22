import logging
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.database_models import (
    get_session, Email, Draft, PromptConfig, ProcessingLog,
    create_tables, Email as EmailModel, Draft as DraftModel
)
from models.email_models import EmailCreate, DraftCreate, PromptConfigCreate

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.session = get_session()
        self._initialize_database()
    def _initialize_database(self):
        try:
            create_tables()
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    def add_email(self, email_data: EmailCreate) -> Optional[EmailModel]:
        try:
            email = Email(
                sender=email_data.sender,
                recipient=email_data.recipient,
                subject=email_data.subject,
                body=email_data.body,
                date=email_data.date,
                message_id=email_data.message_id,
                created_at=datetime.utcnow()
            )
            self.session.add(email)
            self.session.commit()
            return email
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding email: {str(e)}")
            return None
    def get_all_emails(self, limit: int = 100, offset: int = 0) -> List[EmailModel]:
        try:
            return self.session.query(Email).order_by(Email.date.desc()).offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting emails: {str(e)}")
            return []
    def get_email(self, email_id: int) -> Optional[EmailModel]:
        try:
            return self.session.query(Email).filter(Email.id == email_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting email {email_id}: {str(e)}")
            return None
    def update_email_processing(self, email_id: int, processing_data: Dict[str, Any]) -> bool:
        try:
            email = self.get_email(email_id)
            if not email:
                return False
            email.category = processing_data.get('category', email.category)
            email.category_confidence = processing_data.get('category_confidence', email.category_confidence)
            email.category_reason = processing_data.get('category_reason', email.category_reason)
            email.action_items = processing_data.get('action_items', email.action_items)
            email.summary = processing_data.get('summary', email.summary)
            email.is_processed = True
            email.processed_at = datetime.utcnow()
            email.updated_at = datetime.utcnow()
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating email {email_id}: {str(e)}")
            return False
    def add_draft(self, draft_data: DraftCreate) -> Optional[DraftModel]:
        try:
            draft = Draft(
                subject=draft_data.subject,
                body=draft_data.body,
                recipient=draft_data.recipient,
                tone=draft_data.tone,
                original_email_id=draft_data.original_email_id,
                generated_by_ai=draft_data.generated_by_ai,
                created_at=datetime.utcnow()
            )
            self.session.add(draft)
            self.session.commit()
            return draft
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding draft: {str(e)}")
            return None
    def get_all_drafts(self) -> List[DraftModel]:
        try:
            return self.session.query(Draft).order_by(Draft.created_at.desc()).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting drafts: {str(e)}")
            return []
    def update_draft(self, draft_id: int, updates: Dict[str, Any]) -> bool:
        try:
            draft = self.session.query(Draft).filter(Draft.id == draft_id).first()
            if not draft:
                return False
            if 'subject' in updates: draft.subject = updates['subject']
            if 'body' in updates: draft.body = updates['body']
            if 'recipient' in updates: draft.recipient = updates['recipient']
            if 'tone' in updates: draft.tone = updates['tone']
            draft.is_edited = True
            draft.updated_at = datetime.utcnow()
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating draft {draft_id}: {str(e)}")
            return False
    def add_prompt_config(self, prompt_data: PromptConfigCreate) -> Optional[PromptConfig]:
        try:
            prompt = PromptConfig(
                name=prompt_data.name,
                prompt_type=prompt_data.prompt_type,
                prompt_text=prompt_data.prompt_text,
                description=prompt_data.description,
                is_custom=prompt_data.is_custom,
                is_active=prompt_data.is_active,
                created_at=datetime.utcnow()
            )
            self.session.add(prompt)
            self.session.commit()
            return prompt
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding prompt config: {str(e)}")
            return None
    def add_processing_log(self, log_data: Dict[str, Any]) -> bool:
        try:
            log = ProcessingLog(
                email_id=log_data.get('email_id'),
                operation=log_data.get('operation'),
                status=log_data.get('status'),
                input_data=log_data.get('input_data'),
                output_data=log_data.get('output_data'),
                error_message=log_data.get('error_message'),
                processing_time=log_data.get('processing_time'),
                llm_model=log_data.get('llm_model'),
                created_at=datetime.utcnow()
            )
            self.session.add(log)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error adding processing log: {str(e)}")
            return False
    def get_processing_logs(self, limit: int = 50) -> List[ProcessingLog]:
        try:
            return self.session.query(ProcessingLog).order_by(ProcessingLog.created_at.desc()).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting processing logs: {str(e)}")
            return []
    def close(self):
        self.session.close()

# Instantiate clean manager
_db_clean = DatabaseManager()

db_manager = _db_clean
