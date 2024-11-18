"""
Data reporting tools.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import json
from pathlib import Path

from ...core.tools import BaseTool


class ReportGenerator(BaseTool):
    """Tool for generating data analysis reports."""
    
    name = "report_generator"
    description = "Generate reports from data analysis results"
    
    def __init__(self):
        super().__init__()
    
    async def save_json(
        self,
        data: Dict[str, Any],
        file_path: str
    ) -> None:
        """Save results as JSON."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def save_csv(
        self,
        data: pd.DataFrame,
        file_path: str
    ) -> None:
        """Save results as CSV."""
        data.to_csv(file_path, index=False)
    
    async def save_excel(
        self,
        data: Dict[str, pd.DataFrame],
        file_path: str
    ) -> None:
        """Save results as Excel with multiple sheets."""
        with pd.ExcelWriter(file_path) as writer:
            for sheet_name, df in data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
