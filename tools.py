import logging
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from pydantic import BaseModel, Field
from typing import Type
from langchain_community.document_loaders import PyPDFLoader
import os

search_tool = SerperDevTool()

class BloodTestReportInput(BaseModel):
    path: str = Field(..., description="Path to the PDF file containing the blood test report")

class BloodTestReportTool(BaseTool):
    name: str = "Blood Test Report Reader"
    description: str = "Tool to read data from a PDF file from a given path. Use this tool to extract the full content of a blood test report PDF."
    args_schema: Type[BaseModel] = BloodTestReportInput

    def _run(self, path: str) -> str:
        """function to read data from a PDF file."""
        
        try:
            # Validate file exists
            if not os.path.exists(path):
                error_msg = f"Error: File not found at path: {path}"
                return error_msg
            
            # Validate it's a PDF file
            if not path.lower().endswith('.pdf'):
                error_msg = f"Error: File must be a PDF. Provided: {path}"
                return error_msg
            
            loader = PyPDFLoader(file_path=path)
            docs = loader.load()

            if not docs:
                error_msg = "Error: No content found in the PDF file."
                return error_msg

            full_report = ""
            for i, data in enumerate(docs):
                # Clean and format the report data
                content = data.page_content
                
                # Remove extra whitespaces and format properly
                while "\n\n" in content:
                    content = content.replace("\n\n", "\n")
                    
                full_report += content + "\n"
            
            return full_report.strip()
            
        except Exception as e:
            error_msg = f"Error reading PDF file: {str(e)}"
            return error_msg
        
blood_test_tool = BloodTestReportTool()