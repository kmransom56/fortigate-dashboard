#!/usr/bin/env python3
"""
Text User Interface (TUI) for AI Assistant

Interactive terminal interface for accessing all AI backends and functions.
"""

import sys
import os
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.markdown import Markdown
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich not installed. Install with: uv pip install rich")
    print("   Falling back to basic interface")

from .simple_ai import (
    get_ai_assistant,
    audit_file,
    repair_code,
    optimize_code,
    learn_from_codebase,
    update_dependencies,
    configure_backend
)
from .config import AIConfig
from .agent_framework_wrapper import AgentBackend


class AIAssistantTUI:
    """Text User Interface for AI Assistant"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.current_backend = None
        self.assistant = None
    
    def print(self, *args, **kwargs):
        """Print with rich if available"""
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)
    
    def show_header(self):
        """Show application header"""
        if RICH_AVAILABLE:
            self.print(Panel.fit(
                "[bold blue]AI Assistant TUI[/bold blue]\n"
                "[dim]Network Observability Platform[/dim]",
                border_style="blue"
            ))
        else:
            print("\n" + "="*60)
            print("AI Assistant TUI - Network Observability Platform")
            print("="*60 + "\n")
    
    def show_status(self):
        """Show current status"""
        backend = AIConfig.detect_backend()
        available = AIConfig.list_available_backends()
        
        if RICH_AVAILABLE:
            table = Table(title="Backend Status", show_header=True, header_style="bold magenta")
            table.add_column("Backend", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Current", style="yellow")
            
            for b in AIConfig.BACKEND_PRIORITY:
                status = "✓ Available" if b in available else "✗ Not Available"
                current = "← Current" if b == backend else ""
                table.add_row(b.value, status, current)
            
            self.print(table)
        else:
            print("\nBackend Status:")
            print(f"Current: {backend.value}")
            print("Available:", [b.value for b in available])
    
    def select_backend(self) -> Optional[AgentBackend]:
        """Interactive backend selection"""
        available = AIConfig.list_available_backends()
        current = AIConfig.detect_backend()
        
        if RICH_AVAILABLE:
            self.print("\n[bold]Select Backend:[/bold]")
        else:
            print("\nSelect Backend:")
        
        options = []
        for i, backend in enumerate(AIConfig.BACKEND_PRIORITY, 1):
            marker = "✓" if backend in available else " "
            current_marker = " ← Current" if backend == current else ""
            
            if RICH_AVAILABLE:
                self.print(f"  {i}. {marker} [cyan]{backend.value}[/cyan]{current_marker}")
            else:
                print(f"  {i}. {marker} {backend.value}{current_marker}")
            
            options.append(backend)
        
        choice = Prompt.ask("\nSelect backend", default="1") if RICH_AVAILABLE else input("\nSelect backend [1]: ").strip() or "1"
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                selected = options[idx]
                AIConfig.set_backend(selected)
                self.current_backend = selected
                return selected
        except (ValueError, IndexError):
            pass
        
        return current
    
    def main_menu(self):
        """Show main menu"""
        while True:
            if RICH_AVAILABLE:
                self.print("\n[bold cyan]Main Menu[/bold cyan]")
                menu = Table.grid(padding=1)
                menu.add_column(style="cyan")
                menu.add_column()
                menu.add_row("1.", "Audit code/file")
                menu.add_row("2.", "Repair issue")
                menu.add_row("3.", "Optimize code")
                menu.add_row("4.", "Learn from codebase")
                menu.add_row("5.", "Update dependencies")
                menu.add_row("6.", "Configure backend")
                menu.add_row("7.", "Show status")
                menu.add_row("0.", "Exit")
                self.print(menu)
            else:
                print("\nMain Menu:")
                print("  1. Audit code/file")
                print("  2. Repair issue")
                print("  3. Optimize code")
                print("  4. Learn from codebase")
                print("  5. Update dependencies")
                print("  6. Configure backend")
                print("  7. Show status")
                print("  0. Exit")
            
            choice = Prompt.ask("\nChoice", default="0") if RICH_AVAILABLE else input("\nChoice [0]: ").strip() or "0"
            
            if choice == "0":
                if RICH_AVAILABLE:
                    self.print("\n[bold green]Goodbye![/bold green]")
                else:
                    print("\nGoodbye!")
                break
            elif choice == "1":
                self.handle_audit()
            elif choice == "2":
                self.handle_repair()
            elif choice == "3":
                self.handle_optimize()
            elif choice == "4":
                self.handle_learn()
            elif choice == "5":
                self.handle_update()
            elif choice == "6":
                self.select_backend()
            elif choice == "7":
                self.show_status()
            else:
                if RICH_AVAILABLE:
                    self.print("[red]Invalid choice[/red]")
                else:
                    print("Invalid choice")
    
    def handle_audit(self):
        """Handle audit operation"""
        target = Prompt.ask("File/directory to audit") if RICH_AVAILABLE else input("File/directory to audit: ").strip()
        if not target or not os.path.exists(target):
            self.print(f"[red]Target not found: {target}[/red]" if RICH_AVAILABLE else f"Target not found: {target}")
            return
        
        audit_types = ["code", "config", "security", "performance", "dependencies"]
        if RICH_AVAILABLE:
            self.print("\nAudit types: " + ", ".join(audit_types))
        audit_type = Prompt.ask("Audit type", default="code") if RICH_AVAILABLE else input(f"Audit type [{audit_types[0]}]: ").strip() or audit_types[0]
        
        self.print("\n[dim]Running audit...[/dim]" if RICH_AVAILABLE else "\nRunning audit...")
        result = audit_file(target, audit_type)
        
        if "error" in result:
            self.print(f"[red]Error: {result['error']}[/red]" if RICH_AVAILABLE else f"Error: {result['error']}")
            return
        
        if RICH_AVAILABLE:
            self.print(Panel(Markdown(result.get('findings', 'No findings')), title="Audit Results", border_style="green"))
        else:
            print("\n" + "="*60)
            print("Audit Results:")
            print("="*60)
            print(result.get('findings', 'No findings'))
    
    def handle_repair(self):
        """Handle repair operation"""
        issue = Prompt.ask("Issue description") if RICH_AVAILABLE else input("Issue description: ").strip()
        if not issue:
            return
        
        file_path = Prompt.ask("File to repair (optional)", default="") if RICH_AVAILABLE else input("File to repair (optional): ").strip()
        file_path = file_path if file_path and os.path.exists(file_path) else None
        
        self.print("\n[dim]Analyzing issue...[/dim]" if RICH_AVAILABLE else "\nAnalyzing issue...")
        result = repair_code(issue, file_path)
        
        if "error" in result:
            self.print(f"[red]Error: {result['error']}[/red]" if RICH_AVAILABLE else f"Error: {result['error']}")
            return
        
        if RICH_AVAILABLE:
            self.print(Panel(Markdown(result.get('fix', 'No fix provided')), title="Repair Solution", border_style="yellow"))
        else:
            print("\n" + "="*60)
            print("Repair Solution:")
            print("="*60)
            print(result.get('fix', 'No fix provided'))
    
    def handle_optimize(self):
        """Handle optimize operation"""
        target = Prompt.ask("File to optimize") if RICH_AVAILABLE else input("File to optimize: ").strip()
        if not target or not os.path.exists(target):
            self.print(f"[red]Target not found: {target}[/red]" if RICH_AVAILABLE else f"Target not found: {target}")
            return
        
        opt_types = ["performance", "memory", "security", "cost"]
        opt_type = Prompt.ask("Optimization type", default="performance") if RICH_AVAILABLE else input(f"Optimization type [{opt_types[0]}]: ").strip() or opt_types[0]
        
        self.print("\n[dim]Analyzing for optimization...[/dim]" if RICH_AVAILABLE else "\nAnalyzing for optimization...")
        result = optimize_code(target, opt_type)
        
        if "error" in result:
            self.print(f"[red]Error: {result['error']}[/red]" if RICH_AVAILABLE else f"Error: {result['error']}")
            return
        
        if RICH_AVAILABLE:
            self.print(Panel(Markdown(result.get('recommendations', 'No recommendations')), title="Optimization Recommendations", border_style="blue"))
        else:
            print("\n" + "="*60)
            print("Optimization Recommendations:")
            print("="*60)
            print(result.get('recommendations', 'No recommendations'))
    
    def handle_learn(self):
        """Handle learn operation"""
        source = Prompt.ask("Source (file/directory)") if RICH_AVAILABLE else input("Source (file/directory): ").strip()
        if not source:
            return
        
        topic = Prompt.ask("Topic (optional)", default="") if RICH_AVAILABLE else input("Topic (optional): ").strip()
        topic = topic if topic else None
        
        self.print("\n[dim]Learning from source...[/dim]" if RICH_AVAILABLE else "\nLearning from source...")
        result = learn_from_codebase(source, topic)
        
        if "error" in result:
            self.print(f"[red]Error: {result['error']}[/red]" if RICH_AVAILABLE else f"Error: {result['error']}")
            return
        
        if RICH_AVAILABLE:
            self.print(Panel(Markdown(result.get('knowledge', 'No knowledge extracted')), title="Learned Knowledge", border_style="magenta"))
        else:
            print("\n" + "="*60)
            print("Learned Knowledge:")
            print("="*60)
            print(result.get('knowledge', 'No knowledge extracted'))
    
    def handle_update(self):
        """Handle update operation"""
        file_path = Prompt.ask("Requirements file (optional)", default="") if RICH_AVAILABLE else input("Requirements file (optional): ").strip()
        file_path = file_path if file_path and os.path.exists(file_path) else None
        
        self.print("\n[dim]Analyzing for updates...[/dim]" if RICH_AVAILABLE else "\nAnalyzing for updates...")
        result = update_dependencies(file_path)
        
        if "error" in result:
            self.print(f"[red]Error: {result['error']}[/red]" if RICH_AVAILABLE else f"Error: {result['error']}")
            return
        
        if RICH_AVAILABLE:
            self.print(Panel(Markdown(result.get('recommendations', 'No recommendations')), title="Update Recommendations", border_style="cyan"))
        else:
            print("\n" + "="*60)
            print("Update Recommendations:")
            print("="*60)
            print(result.get('recommendations', 'No recommendations'))
    
    def run(self):
        """Run the TUI"""
        self.show_header()
        self.show_status()
        
        # Get or select backend
        assistant = get_ai_assistant(auto_setup=False)
        if not assistant or not assistant.agent.is_available():
            if RICH_AVAILABLE:
                self.print("\n[yellow]⚠️  No backend available. Please configure one.[/yellow]")
            else:
                print("\n⚠️  No backend available. Please configure one.")
            self.select_backend()
        
        self.main_menu()


def main():
    """Main entry point"""
    tui = AIAssistantTUI()
    try:
        tui.run()
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            tui.print("\n\n[bold red]Interrupted[/bold red]")
        else:
            print("\n\nInterrupted")
    except Exception as e:
        if RICH_AVAILABLE:
            tui.print(f"\n[red]Error: {e}[/red]")
        else:
            print(f"\nError: {e}")


if __name__ == "__main__":
    main()
