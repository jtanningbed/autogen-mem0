"""
Data loading tools.
"""

from typing import Dict, Any, Optional
import pandas as pd

from ...core.tools import BaseTool


class DataLoader(BaseTool):
    """Tool for loading data from various sources."""
    
    name = "data_loader"
    description = "Load data from various file formats and sources"
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['csv', 'json', 'parquet', 'excel']
    
    async def load_file(
        self,
        file_path: str,
        format: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Load data from a file."""
        if format is None:
            format = file_path.split('.')[-1].lower()
            
        if format not in self.supported_formats:
            raise ValueError(f"Unsupported format: {format}")
            
        if format == 'csv':
            return pd.read_csv(file_path, **kwargs)
        elif format == 'json':
            return pd.read_json(file_path, **kwargs)
        elif format == 'parquet':
            return pd.read_parquet(file_path, **kwargs)
        elif format == 'excel':
            return pd.read_excel(file_path, **kwargs)
            
        raise ValueError(f"Format {format} is supported but not implemented")
