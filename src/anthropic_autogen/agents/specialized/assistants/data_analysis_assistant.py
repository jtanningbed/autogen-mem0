"""
Data analysis assistant agent implementation.
Specializes in data analysis, visualization, and reporting tasks.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from ....core.agents import BaseToolAgent
from ....core.messaging import ChatMessage, TaskMessage, SystemMessage, MessageCommon as Message
from ....tools.data import (
    DataLoader,
    DataAnalyzer,
    DataVisualizer,
    ReportGenerator
)

class DataAnalysisAssistant(BaseToolAgent):
    """
    Specialized agent for data analysis tasks.
    Provides capabilities for data processing, statistical analysis,
    and visualization.
    """

    def __init__(
        self,
        agent_id: str,
        name: str = "Data Analyst",
        llm_client: Any = None,  # Type will be ChatCompletionClient
        **kwargs
    ):
        tools = [
            DataLoader(),
            DataAnalyzer(),
            DataVisualizer(),
            ReportGenerator()
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            description="Data analysis and visualization specialist",
            tools=tools,
            **kwargs
        )
        self.llm = llm_client
        self.active_datasets: Dict[str, pd.DataFrame] = {}

    def register_tools(self) -> None:
        """Register data analysis tools."""
        self.tools = {
            "load_data": DataLoader(),
            "describe_data": DataAnalyzer(),
            "analyze_data": DataAnalyzer(),
            "visualize_data": DataVisualizer(),
            "generate_report": ReportGenerator()
        }

    async def load_data(
        self,
        file_path: str,
        dataset_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Load data from various file formats."""
        try:
            # Determine file type and load accordingly
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, **kwargs)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, **kwargs)
            elif file_path.endswith('.json'):
                df = pd.read_json(file_path, **kwargs)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")

            # Generate dataset ID if not provided
            if dataset_id is None:
                dataset_id = f"dataset_{len(self.active_datasets)}"

            self.active_datasets[dataset_id] = df

            return {
                "dataset_id": dataset_id,
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict()
            }

        except Exception as e:
            return {"error": str(e)}

    async def describe_data(
        self,
        dataset_id: str,
        columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate descriptive statistics for the dataset."""
        if dataset_id not in self.active_datasets:
            return {"error": f"Dataset {dataset_id} not found"}

        df = self.active_datasets[dataset_id]
        if columns:
            df = df[columns]

        return {
            "summary": df.describe().to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "unique_values": df.nunique().to_dict()
        }

    async def clean_data(
        self,
        dataset_id: str,
        operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Clean and preprocess data."""
        if dataset_id not in self.active_datasets:
            return {"error": f"Dataset {dataset_id} not found"}

        df = self.active_datasets[dataset_id].copy()
        results = {}

        for op in operations:
            op_type = op.get("type")
            try:
                if op_type == "drop_na":
                    df = df.dropna(**op.get("params", {}))
                elif op_type == "fill_na":
                    df = df.fillna(**op.get("params", {}))
                elif op_type == "drop_duplicates":
                    df = df.drop_duplicates(**op.get("params", {}))
                elif op_type == "replace":
                    df = df.replace(**op.get("params", {}))
                else:
                    results[op_type] = {"error": "Unsupported operation"}
                    continue

                results[op_type] = {"success": True}

            except Exception as e:
                results[op_type] = {"error": str(e)}

        # Store cleaned dataset
        clean_dataset_id = f"{dataset_id}_cleaned"
        self.active_datasets[clean_dataset_id] = df

        return {
            "new_dataset_id": clean_dataset_id,
            "operations_results": results,
            "shape": df.shape
        }

    async def analyze_data(
        self,
        dataset_id: str,
        analysis_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform various types of data analysis."""
        if dataset_id not in self.active_datasets:
            return {"error": f"Dataset {dataset_id} not found"}

        df = self.active_datasets[dataset_id]
        
        try:
            if analysis_type == "correlation":
                return {
                    "correlation_matrix": df.corr().to_dict(),
                    "method": parameters.get("method", "pearson")
                }
            
            elif analysis_type == "groupby":
                group_cols = parameters.get("group_by", [])
                agg_dict = parameters.get("aggregations", {})
                result = df.groupby(group_cols).agg(agg_dict)
                return {"grouped_data": result.to_dict()}
            
            elif analysis_type == "time_series":
                date_col = parameters.get("date_column")
                value_col = parameters.get("value_column")
                freq = parameters.get("frequency", "D")
                
                df[date_col] = pd.to_datetime(df[date_col])
                result = df.set_index(date_col)[value_col].resample(freq).agg(
                    parameters.get("aggregation", "mean")
                )
                return {"time_series_data": result.to_dict()}
            
            else:
                return {"error": f"Unsupported analysis type: {analysis_type}"}

        except Exception as e:
            return {"error": str(e)}

    async def visualize_data(
        self,
        dataset_id: str,
        viz_type: str,
        parameters: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create data visualizations."""
        if dataset_id not in self.active_datasets:
            return {"error": f"Dataset {dataset_id} not found"}

        df = self.active_datasets[dataset_id]
        
        try:
            plt.figure(figsize=parameters.get("figsize", (10, 6)))
            
            if viz_type == "scatter":
                sns.scatterplot(
                    data=df,
                    x=parameters["x"],
                    y=parameters["y"],
                    hue=parameters.get("hue"),
                    style=parameters.get("style")
                )
            
            elif viz_type == "line":
                sns.lineplot(
                    data=df,
                    x=parameters["x"],
                    y=parameters["y"],
                    hue=parameters.get("hue")
                )
            
            elif viz_type == "histogram":
                sns.histplot(
                    data=df,
                    x=parameters["x"],
                    bins=parameters.get("bins", 30),
                    kde=parameters.get("kde", False)
                )
            
            elif viz_type == "boxplot":
                sns.boxplot(
                    data=df,
                    x=parameters.get("x"),
                    y=parameters["y"],
                    hue=parameters.get("hue")
                )
            
            else:
                return {"error": f"Unsupported visualization type: {viz_type}"}

            plt.title(parameters.get("title", ""))
            plt.xlabel(parameters.get("xlabel", ""))
            plt.ylabel(parameters.get("ylabel", ""))
            
            if save_path:
                plt.savefig(save_path)
                plt.close()
                return {"plot_saved": save_path}
            else:
                plt.close()
                return {"message": "Plot displayed"}

        except Exception as e:
            return {"error": str(e)}

    async def statistical_test(
        self,
        dataset_id: str,
        test_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform statistical tests."""
        if dataset_id not in self.active_datasets:
            return {"error": f"Dataset {dataset_id} not found"}

        df = self.active_datasets[dataset_id]
        
        try:
            from scipy import stats
            
            if test_type == "ttest":
                group1 = df[parameters["column"]][
                    df[parameters["group_column"]] == parameters["group1"]
                ]
                group2 = df[parameters["column"]][
                    df[parameters["group_column"]] == parameters["group2"]
                ]
                stat, pval = stats.ttest_ind(group1, group2)
                return {
                    "test": "Independent t-test",
                    "statistic": stat,
                    "p_value": pval
                }
            
            elif test_type == "chi2":
                contingency_table = pd.crosstab(
                    df[parameters["column1"]],
                    df[parameters["column2"]]
                )
                stat, pval, dof, expected = stats.chi2_contingency(
                    contingency_table
                )
                return {
                    "test": "Chi-square test of independence",
                    "statistic": stat,
                    "p_value": pval,
                    "dof": dof
                }
            
            elif test_type == "anova":
                groups = [
                    df[parameters["value_column"]][
                        df[parameters["group_column"]] == group
                    ]
                    for group in parameters["groups"]
                ]
                stat, pval = stats.f_oneway(*groups)
                return {
                    "test": "One-way ANOVA",
                    "statistic": stat,
                    "p_value": pval
                }
            
            else:
                return {"error": f"Unsupported test type: {test_type}"}

        except Exception as e:
            return {"error": str(e)}

    async def generate_report(
        self,
        dataset_id: str,
        report_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate analysis reports."""
        if dataset_id not in self.active_datasets:
            return {"error": f"Dataset {dataset_id} not found"}

        df = self.active_datasets[dataset_id]
        
        try:
            if report_type == "summary":
                report = {
                    "dataset_info": {
                        "shape": df.shape,
                        "columns": df.columns.tolist(),
                        "dtypes": df.dtypes.to_dict()
                    },
                    "descriptive_stats": df.describe().to_dict(),
                    "missing_values": df.isnull().sum().to_dict(),
                    "correlations": df.corr().to_dict() if parameters.get(
                        "include_correlations", True
                    ) else None
                }
            
            elif report_type == "custom":
                report = {}
                if parameters.get("include_summary", True):
                    report["summary"] = df.describe().to_dict()
                
                if parameters.get("group_analysis"):
                    group_col = parameters["group_analysis"]["column"]
                    metrics = parameters["group_analysis"].get(
                        "metrics", ["mean", "count"]
                    )
                    report["group_analysis"] = df.groupby(group_col).agg(
                        metrics
                    ).to_dict()
                
                if parameters.get("custom_calculations"):
                    report["calculations"] = {}
                    for calc in parameters["custom_calculations"]:
                        if calc["type"] == "count_unique":
                            report["calculations"][calc["name"]] = df[
                                calc["column"]
                            ].nunique()
                        elif calc["type"] == "percentage":
                            report["calculations"][calc["name"]] = df[
                                calc["column"]
                            ].value_counts(normalize=True).to_dict()
            
            else:
                return {"error": f"Unsupported report type: {report_type}"}

            return {"report": report}

        except Exception as e:
            return {"error": str(e)}
