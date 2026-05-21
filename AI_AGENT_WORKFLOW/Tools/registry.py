#this file deals with the registry of tools that are available for the agent to use. It contains the ToolRegistry class which is used to register the tools and get the tool by name when it is being executed by the agent. The registry is a dictionary that maps the name of the tool to the tool object. This allows us to easily get the tool by name when it is being executed by the agent and also to display the list of available tools in the tool box when we are using openai api to display the tools in the tool box.
import logging
from pathlib import Path
from typing import Any
from Tools.base import Tool, ToolInvokation, ToolResult
from Tools.builtin import ReadFileTool, get_all_builtin_tools
from Tools.subagents import SubAgentTool, get_default_subagents_definitions
from config.config import Config
from Tools.builtin.rag import RAGTool 
from client.llm_client import LLMClient


logger = logging.getLogger(__name__) #logging is important for debugging and also for understanding the flow of the program. We will use logging to log the registration of tools and also to log any errors that occur during the registration of tools.
class ToolRegistry:
    def __init__(self,config:Config):
        self._tools: dict[str, Tool] = {}#this creates a dictionary that maps the name of the tool to the tool object. This allows us to easily get the tool by name when it is being executed by the agent and also to display the list of available tools in the tool box when we are using openai api to display the tools in the tool box.
        self.config = config

    def register(self, tool: Tool):
        if tool.name in self._tools:
            logger.warning(f"Tool with name {tool.name} is already registered. Overwriting the existing tool.")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def unregister(self, name: str):
        if name in self._tools:
            del self._tools[name]
            logger.debug(f"Unregistered tool: {name}")
            return True
        else:
            logger.warning(f"Tool with name {name} is not registered. Cannot unregister.")
            return False
    def get(self, name: str) -> Tool | None:
        if name in self._tools:
            return self._tools[name]
        return None

    def get_tools(self) -> list[Tool]:
        tools: list[Tool] = []
        for tool in self._tools.values(): # this will iterate over the values of the dictionary which are the tool objects and append them to the tools list and then return the tools list.
            tools.append(tool)
        if self.config.allowed_tools:
            allowed_set = set(self.config.allowed_tools)
            tools = [t for t in tools if t.name in allowed_set]
        return tools
    def get_schema(self) -> list[dict[str, Any]]:
        return [tool.to_openai_schema() for tool in self.get_tools()]
    async def invoke(self, name: str, params:dict[str, Any], cwd:Path) -> ToolResult:
        tool = self.get(name)
        if tool is None:
            return ToolResult.error_result(
                f"Unknown tool {name}",
                metadata={"tool_name: " :name}
            )
            
        validate_errors = tool.validate_params(params)
        if validate_errors:
            return ToolResult.error_result(
                f"Invalid Parameter :{' '.join(validate_errors)}",
            )
            
        Invokation = ToolInvokation(
            cwd=cwd,
            params=params
        )
        try:
           result = await tool.execute(Invokation)
        except Exception as e:
            logger.exception(f"Tool {name} raised an unexpected error")
            result = ToolResult.error_result(
                f"internal error {e}",metadata={f"Tool_name": name}
            )
        return result




def create_default_registry(config:Config) -> ToolRegistry:
    registry = ToolRegistry(config)
    llm_client = LLMClient(config)
    for tool_class in get_all_builtin_tools():
        if tool_class == RAGTool:
            registry.register(tool_class(config, llm_client))  
        else:
            registry.register(tool_class(config))
    for subagent_def in get_default_subagents_definitions():
        registry.register(SubAgentTool(config, subagent_def))
    return registry


