# AI Healer Code Quality Commands

## Overview

The AI Healer service now includes methods to automatically check and fix code quality issues. These commands can be used by the AI healer to diagnose and fix code problems.

---

## Available Commands

### 1. `check_syntax(file_paths)`

Check Python files for syntax errors using the syntax checker.

**Usage**:
```python
from app.services.ai_healer import get_ai_healer

healer = get_ai_healer()
result = healer.check_syntax(["app/main.py", "app/services/"])
```

**Returns**:
```python
{
    "timestamp": "2025-01-XX...",
    "command": "syntax_check",
    "files_checked": [],
    "errors_found": [],
    "passed": True,
    "returncode": 0,
    "stdout": "...",
    "stderr": "..."
}
```

**When to use**: Always run this first before formatting or linting.

---

### 2. `format_code(file_paths)`

Format code using Black.

**Usage**:
```python
healer = get_ai_healer()
result = healer.format_code(["app/main.py", "app/services/"])
```

**Returns**:
```python
{
    "timestamp": "2025-01-XX...",
    "command": "format_code",
    "files_formatted": ["reformatted app/main.py"],
    "passed": True,
    "returncode": 0,
    "stdout": "...",
    "stderr": "..."
}
```

**When to use**: After syntax check passes, to auto-fix formatting issues.

---

### 3. `lint_code(file_paths)`

Lint code using Flake8.

**Usage**:
```python
healer = get_ai_healer()
result = healer.lint_code(["app/main.py", "app/services/"])
```

**Returns**:
```python
{
    "timestamp": "2025-01-XX...",
    "command": "lint_code",
    "issues_found": ["app/main.py:42:1: F401 'os' imported but unused"],
    "passed": True,
    "returncode": 0,
    "stdout": "...",
    "stderr": "..."
}
```

**When to use**: After syntax check and formatting, to find style issues.

---

### 4. `run_code_quality_checks(file_paths, auto_fix=True)`

Run comprehensive code quality checks (syntax, format, lint) in the correct order.

**Usage**:
```python
healer = get_ai_healer()
result = healer.run_code_quality_checks(["app/"], auto_fix=True)
```

**Returns**:
```python
{
    "timestamp": "2025-01-XX...",
    "command": "code_quality_checks",
    "syntax_check": {...},
    "format_check": {...},
    "lint_check": {...},
    "all_passed": True
}
```

**When to use**: For comprehensive code quality validation.

---

### 5. `auto_fix_code_issues(file_paths)`

Automatically fix code issues that can be auto-fixed (formatting, etc.).

**Usage**:
```python
healer = get_ai_healer()
result = healer.auto_fix_code_issues(["app/main.py"])
```

**Returns**:
```python
{
    "timestamp": "2025-01-XX...",
    "command": "auto_fix_code_issues",
    "fixed": ["Formatted: reformatted app/main.py"],
    "needs_manual_fix": ["Syntax error: ..."],
    "passed": True,
    "quality_check_results": {...}
}
```

**When to use**: When you want the AI healer to automatically fix what it can.

---

## Integration with Error Diagnosis

The AI healer automatically suggests code quality fixes when it detects:

- **Syntax errors**: Suggests running `check_syntax()`
- **Formatting issues**: Suggests running `format_code()` (auto-fixable)
- **Linting issues**: Suggests running `lint_code()` (manual review needed)

---

## Example: Auto-Fix Workflow

```python
from app.services.ai_healer import get_ai_healer

healer = get_ai_healer()

# Detect error
error_msg = "SyntaxError: unexpected indent (file.py, line 42)"
diagnosis = healer.diagnose(error_msg)

if diagnosis["matches_found"]:
    # Run auto-fix
    result = healer.auto_fix_code_issues(["app/"])
    
    if result["passed"]:
        print("✅ All issues fixed automatically")
    else:
        print("⚠️ Some issues need manual fixing:")
        for issue in result["needs_manual_fix"]:
            print(f"  - {issue}")
```

---

## Knowledge Base Integration

The knowledge base (`app/data/healer_knowledge_base.json`) now includes:

1. **Syntax error patterns** - Detects common syntax errors
2. **Code quality patterns** - Detects formatting/linting issues
3. **Command references** - Documents available commands

---

## API Endpoint Integration

These commands can be called via the `/api/report-error` endpoint:

```bash
curl -X POST http://localhost:8000/api/report-error \
  -H "Content-Type: application/json" \
  -d '{
    "error": "SyntaxError: unexpected indent",
    "category": "syntax_error",
    "file": "app/main.py"
  }'
```

The AI healer will:
1. Diagnose the error
2. Suggest fixes
3. If auto-remediable, run `auto_fix_code_issues()`

---

## Best Practices

1. **Always check syntax first** - Syntax errors prevent code from running
2. **Format before linting** - Black fixes many issues that flake8 would flag
3. **Review linting issues** - Some require manual fixes
4. **Use comprehensive check** - `run_code_quality_checks()` runs everything in order

---

## Troubleshooting

### Command not found errors

If you see "command not found" errors:
- Ensure `tools/utils/check_syntax.py` exists
- Ensure `black` and `flake8` are installed: `pip install black flake8`

### Timeout errors

Commands have timeouts (60-120 seconds). For large codebases:
- Check specific files instead of entire directories
- Run checks in smaller batches

### Permission errors

Ensure scripts are executable:
```bash
chmod +x tools/utils/check_syntax.py
chmod +x scripts/check_code_quality.sh
```

---

## Summary

The AI Healer now has full code quality checking capabilities:

✅ **Syntax checking** - Catches syntax errors  
✅ **Code formatting** - Auto-fixes formatting  
✅ **Code linting** - Finds style issues  
✅ **Comprehensive checks** - Runs all checks in order  
✅ **Auto-fix** - Automatically fixes what it can  

These commands are integrated into the knowledge base and can be automatically triggered when errors are detected.
