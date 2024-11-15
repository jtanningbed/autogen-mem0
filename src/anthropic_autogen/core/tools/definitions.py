from .schema import ToolSchema, ToolParameter

EDITOR_TOOL = ToolSchema(
    name="editor",
    description="Edit or create files",
    parameters={
        "path": ToolParameter(
            type="string",
            description="Path to file",
            required=True
        ),
        "content": ToolParameter(
            type="string",
            description="Content to write",
            required=False
        ),
        "mode": ToolParameter(
            type="string",
            description="Edit mode",
            enum=["write", "append", "modify"],
            default="write"
        )
    }
)

SHELL_TOOL = ToolSchema(
    name="shell",
    description="Execute shell commands",
    parameters={
        "command": ToolParameter(
            type="string",
            description="Command to execute",
            required=True
        ),
        "working_dir": ToolParameter(
            type="string",
            description="Working directory",
            required=False
        ),
        "timeout": ToolParameter(
            type="number",
            description="Command timeout in seconds",
            required=False,
            default=60.0
        )
    }
)

MERMAID_TOOL = ToolSchema(
    name="mermaid",
    description="Generate Mermaid diagrams",
    parameters={
        "diagram_type": ToolParameter(
            type="string",
            description="Type of diagram",
            enum=["flowchart", "sequence", "class", "state"],
            required=True
        ),
        "content": ToolParameter(
            type="string",
            description="Mermaid diagram definition",
            required=True
        ),
        "output_path": ToolParameter(
            type="string",
            description="Output file path",
            required=False
        )
    }
)
