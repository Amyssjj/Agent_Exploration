"""File QA Tool, for answer the questions about File"""

from typing import Any, Dict, List, Optional, Union, Literal, ClassVar
import os
import shutil
import traceback
import langfun as lf
from langfun.core.agentic import action as action_lib
import pyglove as pg


class FileQA(lf.agentic.Action):
    """This is a tool that can answer questions about a file."""
    file_path: str
    question: str

    allow_symbolic_assignment = True  

    def call(self, session: lf.agentic.Session, *, lm: lf.LanguageModel, **kwargs) -> str:
        # Load the file
        try:
            file_content = lf.Mime.from_uri(self.file_path)
            if file_content.is_text:
                file_content = file_content.to_text()
            else:
                file_content = f"[Non-text file of type: {file_content.mime_type}]"

            # Ask the question
            with session.phase("query_processing"):
                session.info(f"Processing file: {self.file_path}")
                response = session.query(
                    "File content:\n{{file_content}}\n\nAnswer the question based on the file content: {{question}}",
                    lm=lm,
                    file_content=file_content,
                    question=self.question
                )
                session.info("Query processing completed")
                return response
        except Exception as e:
            session.error(f"Error loading file: {str(e)}")
            return f"Error: Could not process file ({str(e)})"