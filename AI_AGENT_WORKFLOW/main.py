# main.py
import asyncio
from pathlib import Path
import sys
from typing import Any
import click
from Agent.agent import Agent
from Agent.events import AgentEventType
from config.config import Config
from config.loader import load_config
from ui.agentui import TUI, get_console


console = get_console()

class CLI:
    def __init__(self, config: Config):
        self.agent: Agent | None = None
        self.config = config
        self.tui = TUI(config, console)
        self.rag_mode = False
        self.rag_collection = None
    
    async def run_single(self, message: str) -> str | None:
        async with Agent(self.config) as agent:
            self.agent = agent
            return await self._process_message(message)
    
    async def run_rag_mode(self, directory: Path):
        """Run in RAG mode - ingest PDFs and allow queries."""
        self.rag_mode = True
        
        console.print("\n[highlight]═══ RAG Mode Activated ═══[/highlight]\n")
        console.print(f"[info]Directory:[/info] {directory}")
        
        async with Agent(self.config) as agent:
            self.agent = agent
            
            # Ingest documents
            console.print("\n[processing]Ingesting PDF documents...[/processing]\n")
            
            ingest_result = await self.agent.session.tool_registry.invoke(
                "rag",
                {
                    "action": "ingest",
                    "directory": str(directory),
                    "strategy": "fast",
                    "recursive": True
                },
                self.config.cwd
            )
            
            if not ingest_result.success:
                console.print(f"[error]Ingestion failed: {ingest_result.error}[/error]")
                return
            
            console.print(f"[success]{ingest_result.output}[/success]\n")
            
            # Store collection name
            self.rag_collection = ingest_result.metadata.get('collection_name')
            
            # Enter query loop
            console.print("[highlight]You can now ask questions about the documents![/highlight]")
            console.print("[dim]Commands: /list (list collections), /switch <name> (switch collection), /exit (quit RAG mode)[/dim]\n")
            
            while True:
                try:
                    question = console.input("\n[user]Question>[/user] ").strip()
                    
                    if not question:
                        continue
                    
                    if question.lower() in ['/exit', '/quit']:
                        console.print("\n[dim]Exiting RAG mode...[/dim]")
                        break
                    
                    if question.lower() == '/list':
                        await self._list_rag_collections()
                        continue
                    
                    if question.lower().startswith('/switch '):
                        collection_name = question[8:].strip()
                        self.rag_collection = collection_name
                        console.print(f"[success]Switched to collection: {collection_name}[/success]")
                        continue
                    
                    # Query the documents
                    await self._query_rag(question)
                
                except KeyboardInterrupt:
                    console.print("\n[dim]Use /exit to quit RAG mode[/dim]")
                except EOFError:
                    break
        
        console.print("\n[dim]RAG mode ended[/dim]")
    
    async def _query_rag(self, question: str):
        """Query the RAG system."""
        if not self.rag_collection:
            console.print("[error]No collection selected[/error]")
            return
        
        console.print(f"\n[processing]Searching documents...[/processing]")
        
        result = await self.agent.session.tool_registry.invoke(
            "rag",
            {
                "action": "query",
                "query": question,
                "collection_name": self.rag_collection,
                "top_k": 3,
                "score_threshold": 0.3
            },
            self.config.cwd
        )
        
        if result.success:
            console.print(f"\n[assistant]{result.output}[/assistant]")
        else:
            console.print(f"\n[error]{result.error}[/error]")
    
    async def _list_rag_collections(self):
        """List available RAG collections."""
        result = await self.agent.session.tool_registry.invoke(
            "rag",
            {"action": "list_collections"},
            self.config.cwd
        )
        
        console.print(f"\n{result.output}")
    
    async def run_interactive(self):
        self.tui.print_welcome(
            'Nexus Agent',
            lines=[
                f"model: {self.config.model_name}",
                f"cwd: {self.config.cwd}",
                f"commands: /help /config /approval /model /rag /exit"
            ]
        )
        
        async with Agent(self.config) as agent:
            self.agent = agent
            
            while True:
                try:
                    user_input = console.input("\n[user]>[/user] ").strip()
                    
                    if not user_input:
                        continue
                    
                    # RAG mode command
                    if user_input.lower().startswith('/rag '):
                        directory = user_input[5:].strip()
                        dir_path = Path(directory)
                        
                        if not dir_path.exists():
                            console.print(f"[error]Directory not found: {directory}[/error]")
                            continue
                        
                        await self.run_rag_mode(dir_path)
                        continue
                    
                    await self._process_message(user_input)
                
                except KeyboardInterrupt:
                    console.print("\n[dim]Use /exit to quit[/dim]")
                except EOFError:
                    break
        
        console.print("\n[dim]Goodbye![/dim]")
    
    def _get_tool_kind(self, tool_name: str) -> str | None:
        tool_kind = None
        tool = self.agent.session.tool_registry.get(tool_name)
        if not tool:
            tool_kind = None
        tool_kind = tool.kind.value
        return tool_kind
    
    async def _process_message(self, message: str) -> str | None:
        if not self.agent:
            return None
        
        assistant_streaming = False
        final_response: str | None = None
        
        async for event in self.agent.run(message):
            if event.type == AgentEventType.TEXT_DELTA:
                content = event.data.get("content", "")
                if not assistant_streaming:
                    self.tui.begin_assistant()
                    assistant_streaming = True
                self.tui.stream_assistant_delta(content)
            
            elif event.type == AgentEventType.TEXT_COMPLETE:
                final_response = event.data.get("content")
                if assistant_streaming:
                    self.tui.end_assistant()
                    assistant_streaming = False
            
            elif event.type == AgentEventType.AGENT_ERROR:
                error = event.data.get("error", "unknown error")
                console.print(f"\n[error]Error {error}[/error]")
            
            elif event.type == AgentEventType.TOOL_CALL_START:
                tool_name = event.data.get("name", "unknown tool")
                tool_kind = self._get_tool_kind(tool_name)
                self.tui.tool_call_start(
                    event.data.get("call_id", ""),
                    tool_name,
                    tool_kind,
                    event.data.get("arguments", {})
                )
            
            elif event.type == AgentEventType.TOOL_CALL_COMPLETE:
                tool_name = event.data.get("name", "unknown")
                tool_kind = self._get_tool_kind(tool_name)
                self.tui.tool_call_complete(
                    event.data.get("call_id", ""),
                    tool_name,
                    tool_kind,
                    event.data.get("success", False),
                    event.data.get("output", ""),
                    event.data.get("error"),
                    event.data.get("metadata"),
                    event.data.get("diff"),
                    event.data.get("truncated", False),
                    event.data.get("exit_code"),
                )
        
        return final_response


@click.command()
@click.argument("prompt", required=False)
@click.option(
    "--cwd",
    "-c",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Current Working directory"
)
@click.option(
    "--rag",
    "-r",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Enable RAG mode with directory containing PDFs"
)
def main(
    prompt: str | None,
    cwd: Path | None,
    rag: Path | None
):
    try:
        config = load_config(cwd=cwd)
    except Exception as e:
        console.print(f"\n[error]Configuration Error: {e}[/error]")
        sys.exit(1)
    
    errors = config.validate()
    if errors:
        for error in errors:
            console.print(f"\n[error]Configuration Error: {error}[/error]")
        sys.exit(1)
    
    cli = CLI(config)
    
    # RAG mode
    if rag:
        asyncio.run(cli.run_rag_mode(rag))
    # Single prompt
    elif prompt:
        result = asyncio.run(cli.run_single(prompt))
        if result is None:
            sys.exit("Failed to get a response from the agent.")
    # Interactive mode
    else:
        asyncio.run(cli.run_interactive())


if __name__ == "__main__":
    main()