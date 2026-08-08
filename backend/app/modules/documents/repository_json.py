import json
import logging
import threading
from typing import List, Dict, Any, Optional

from app.core.config import settings
from app.modules.documents.schemas import Document, ChangeReport

logger = logging.getLogger(__name__)

class DocumentRepository:
    def __init__(self):
        self.documents_file = settings.DOCUMENTS_FILE
        self.change_report_file = settings.CHANGE_REPORT_FILE
        self._lock = threading.Lock()

    def _read_json_file(self, filepath: str) -> Any:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from {filepath}: {e}")
            return None

    def _write_json_file(self, filepath: str, data: Any):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load_documents(self) -> List[Document]:
        """Loads all documents from the JSON store."""
        with self._lock:
            data = self._read_json_file(self.documents_file)
            if data is None:
                return []
            return [Document(**doc) for doc in data]

    def save_documents(self, documents: List[Document]):
        """Saves documents to the JSON store."""
        with self._lock:
            data = [doc.model_dump(by_alias=True) for doc in documents]
            self._write_json_file(self.documents_file, data)
            logger.info(f"Saved {len(documents)} documents to {self.documents_file}")

    def load_change_report(self) -> Optional[ChangeReport]:
        """Loads the last change report."""
        with self._lock:
            data = self._read_json_file(self.change_report_file)
            if data is None:
                return None
            return ChangeReport(**data)

    def save_change_report(self, report: ChangeReport):
        """Saves the change report to the JSON store."""
        with self._lock:
            self._write_json_file(self.change_report_file, report.model_dump(by_alias=True))
            logger.info(f"Saved change report to {self.change_report_file}")

document_repository = DocumentRepository()
