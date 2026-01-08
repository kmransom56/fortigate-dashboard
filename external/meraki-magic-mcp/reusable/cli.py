#!/usr/bin/env python3
"""
Command-Line Interface for AI Assistant

Easy-to-use CLI for AI-assisted operations.
"""

import sys
import argparse
from pathlib import Path

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


def cmd_configure(args):
    """Configure backend"""
    configure_backend(args.backend)


def cmd_audit(args):
    """Audit code or configuration"""
    result = audit_file(args.target, args.type)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return 1
    
    print(f"\n✅ Audit completed: {args.target}")
    print(f"Type: {result.get('audit_type', 'unknown')}")
    print("\n" + "="*60)
    print("Findings:")
    print("="*60)
    print(result.get('findings', 'No findings'))
    
    if result.get('recommendations'):
        print("\n" + "="*60)
        print("Recommendations:")
        print("="*60)
        for rec in result['recommendations']:
            print(f"  • {rec}")
    
    return 0


def cmd_repair(args):
    """Repair issues"""
    result = repair_code(args.issue, args.file)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return 1
    
    print(f"\n✅ Repair analysis completed")
    print("\n" + "="*60)
    print("Fix:")
    print("="*60)
    print(result.get('fix', 'No fix provided'))
    
    if result.get('suggested_changes'):
        print("\n" + "="*60)
        print("Suggested Code Changes:")
        print("="*60)
        for lang, code in result['suggested_changes'].items():
            print(f"\n{lang}:")
            print(code)
    
    return 0


def cmd_optimize(args):
    """Optimize code"""
    result = optimize_code(args.target, args.type)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return 1
    
    print(f"\n✅ Optimization analysis completed: {args.target}")
    print("\n" + "="*60)
    print("Recommendations:")
    print("="*60)
    print(result.get('recommendations', 'No recommendations'))
    
    return 0


def cmd_learn(args):
    """Learn from codebase"""
    result = learn_from_codebase(args.source, args.topic)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return 1
    
    print(f"\n✅ Learning completed: {args.source}")
    if args.topic:
        print(f"Topic: {args.topic}")
    print("\n" + "="*60)
    print("Knowledge:")
    print("="*60)
    print(result.get('knowledge', 'No knowledge extracted'))
    
    if result.get('stored'):
        print("\n✓ Knowledge saved to knowledge base")
    
    return 0


def cmd_update(args):
    """Update dependencies"""
    result = update_dependencies(args.file)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return 1
    
    print(f"\n✅ Update analysis completed")
    print("\n" + "="*60)
    print("Recommendations:")
    print("="*60)
    print(result.get('recommendations', 'No recommendations'))
    
    if result.get('action_items'):
        print("\n" + "="*60)
        print("Action Items:")
        print("="*60)
        for item in result['action_items']:
            print(f"  • {item}")
    
    return 0


def cmd_status(args):
    """Show current configuration status"""
    print("\n" + "="*60)
    print("AI Assistant Status")
    print("="*60)
    
    # Current backend
    backend = AIConfig.detect_backend()
    print(f"\nCurrent Backend: {backend.value}")
    
    # Available backends
    available = AIConfig.list_available_backends()
    print(f"\nAvailable Backends ({len(available)}):")
    for b in available:
        print(f"  ✓ {b.value}")
    
    # Test assistant
    print("\nTesting Assistant...")
    assistant = get_ai_assistant(auto_setup=False)
    if assistant and assistant.agent.is_available():
        print("  ✓ Assistant is ready and working")
        print(f"  ✓ Backend: {assistant.agent.get_backend_name()}")
    else:
        print("  ✗ Assistant not available")
        print("  Run 'configure' to set up API keys")
    
    # Config file location
    print(f"\nConfig File: {AIConfig.DEFAULT_CONFIG_FILE}")
    if AIConfig.DEFAULT_CONFIG_FILE.exists():
        print("  ✓ Config file exists")
    else:
        print("  (Config file will be created on first use)")
    
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AI Assistant CLI - Audit, repair, update, optimize, and learn",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s configure                    # Configure backend
  %(prog)s status                        # Show status
  %(prog)s audit app/main.py             # Audit code
  %(prog)s audit app/config.json security  # Security audit
  %(prog)s repair "Function is slow" app/main.py  # Repair issue
  %(prog)s optimize app/main.py          # Optimize performance
  %(prog)s learn app/ architecture       # Learn from codebase
  %(prog)s update requirements.txt       # Update dependencies
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Configure command
    p_configure = subparsers.add_parser('configure', help='Configure backend')
    p_configure.add_argument('backend', nargs='?', help='Backend name (openai, anthropic, etc.)')
    p_configure.set_defaults(func=cmd_configure)
    
    # Status command
    p_status = subparsers.add_parser('status', help='Show configuration status')
    p_status.set_defaults(func=cmd_status)
    
    # Audit command
    p_audit = subparsers.add_parser('audit', help='Audit code or configuration')
    p_audit.add_argument('target', help='File or directory to audit')
    p_audit.add_argument('type', nargs='?', default='code',
                        choices=['code', 'config', 'security', 'performance', 'dependencies'],
                        help='Type of audit (default: code)')
    p_audit.set_defaults(func=cmd_audit)
    
    # Repair command
    p_repair = subparsers.add_parser('repair', help='Repair issues in code')
    p_repair.add_argument('issue', help='Description of issue to fix')
    p_repair.add_argument('file', nargs='?', help='File to repair (optional)')
    p_repair.set_defaults(func=cmd_repair)
    
    # Optimize command
    p_optimize = subparsers.add_parser('optimize', help='Optimize code')
    p_optimize.add_argument('target', help='File to optimize')
    p_optimize.add_argument('type', nargs='?', default='performance',
                           choices=['performance', 'memory', 'security', 'cost'],
                           help='Type of optimization (default: performance)')
    p_optimize.set_defaults(func=cmd_optimize)
    
    # Learn command
    p_learn = subparsers.add_parser('learn', help='Learn from codebase')
    p_learn.add_argument('source', help='Directory or file to learn from')
    p_learn.add_argument('topic', nargs='?', help='Topic to focus on (optional)')
    p_learn.set_defaults(func=cmd_learn)
    
    # Update command
    p_update = subparsers.add_parser('update', help='Update dependencies')
    p_update.add_argument('file', nargs='?', help='Requirements file (optional)')
    p_update.set_defaults(func=cmd_update)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
