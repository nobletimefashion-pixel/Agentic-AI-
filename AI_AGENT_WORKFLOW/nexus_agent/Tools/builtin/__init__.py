from nexus_agent.Tools.builtin.edit_file import EditTool
from nexus_agent.Tools.builtin.glob import GlobTool
from nexus_agent.Tools.builtin.grep import GrepTool
from nexus_agent.Tools.builtin.list_dir import ListDirTool
from nexus_agent.Tools.builtin.memory import MemoryTool
from nexus_agent.Tools.builtin.rag import RAGTool
from nexus_agent.Tools.builtin.read_file import ReadFileTool
from nexus_agent.Tools.builtin.shell import ShellTool
from nexus_agent.Tools.builtin.todo import TodosTool
from nexus_agent.Tools.builtin.web_fetch import WebFetchTool
from nexus_agent.Tools.builtin.web_search import WebSearchTool
from nexus_agent.Tools.builtin.write_file import WriteFileTool

__all__ = ["ReadFileTool","WriteFileTool","EditTool","ShellTool","ListDirTool","GrepTool","GlobTool","WebSearchTool","WebFetchTool","TodosTool","MemoryTool","RagTool"]

def get_all_builtin_tools() -> list[type]:
    return [
        ReadFileTool,
        WriteFileTool,
        EditTool,
        ShellTool,
        ListDirTool,
        GrepTool,
        GlobTool,
        WebSearchTool,
        WebFetchTool,
        TodosTool,
        MemoryTool,
        RAGTool,
        #now whenever we want to add a tool will register it here
    ]