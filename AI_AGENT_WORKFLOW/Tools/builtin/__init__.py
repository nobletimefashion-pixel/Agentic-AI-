from Tools.builtin.edit_file import EditTool
from Tools.builtin.glob import GlobTool
from Tools.builtin.grep import GrepTool
from Tools.builtin.list_dir import ListDirTool
from Tools.builtin.memory import MemoryTool
from Tools.builtin.rag import RAGTool
from Tools.builtin.read_file import ReadFileTool
from Tools.builtin.shell import ShellTool
from Tools.builtin.todo import TodosTool
from Tools.builtin.web_fetch import WebFetchTool
from Tools.builtin.web_search import WebSearchTool
from Tools.builtin.write_file import WriteFileTool

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