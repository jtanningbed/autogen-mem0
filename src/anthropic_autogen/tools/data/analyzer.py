"""
Data analysis tools.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from ...core.tools import BaseTool


class DataAnalyzer(BaseTool):
    """Tool for analyzing data."""
    
    name = "data_analyzer"
    description = "Analyze data using statistical and machine learning methods"
    
    def __init__(self):
        super().__init__()
    
    async def describe(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get descriptive statistics for the data."""
        if columns is not None:
            data = data[columns]
        return data.describe().to_dict()
    
    async def correlate(
        self,
        data: pd.DataFrame,
        columns: Optional[List[str]] = None,
        method: str = 'pearson'
    ) -> Dict[str, Any]:
        """Calculate correlations between columns."""
        if columns is not None:
            data = data[columns]
        return data.corr(method=method).to_dict()
    
    async def aggregate(
        self,
        data: pd.DataFrame,
        group_by: List[str],
        agg_funcs: Dict[str, List[str]]
    ) -> pd.DataFrame:
        """Aggregate data by groups."""
        return data.groupby(group_by).agg(agg_funcs)
