"""
Data visualization tools.
"""

from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from ...core.tools import BaseTool


class DataVisualizer(BaseTool):
    """Tool for creating data visualizations."""
    
    name = "data_visualizer"
    description = "Create data visualizations using matplotlib and seaborn"
    
    def __init__(self):
        super().__init__()
        self.style = 'seaborn'
        plt.style.use(self.style)
    
    async def plot(
        self,
        data: pd.DataFrame,
        kind: str,
        x: Optional[str] = None,
        y: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a plot and return it as a base64 encoded string."""
        plt.figure()
        
        if kind == 'scatter':
            sns.scatterplot(data=data, x=x, y=y, **kwargs)
        elif kind == 'line':
            sns.lineplot(data=data, x=x, y=y, **kwargs)
        elif kind == 'bar':
            sns.barplot(data=data, x=x, y=y, **kwargs)
        elif kind == 'hist':
            sns.histplot(data=data, x=x, **kwargs)
        elif kind == 'box':
            sns.boxplot(data=data, x=x, y=y, **kwargs)
        elif kind == 'violin':
            sns.violinplot(data=data, x=x, y=y, **kwargs)
        else:
            raise ValueError(f"Unsupported plot kind: {kind}")
            
        # Save plot to bytes buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        plt.close()
        
        # Convert to base64
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(image_png).decode()
