# Code Quality Process

## Why Black and Flake8 Don't Catch Syntax Errors

**Important**: `black` and `flake8` do **NOT** catch syntax errors. They only check:
- **Black**: Code formatting (indentation, spacing, line length)
- **Flake8**: Code style (PEP 8 violations, unused imports, etc.)

**Syntax errors** (like incorrect indentation, missing colons, unmatched brackets) require:
- `py_compile` - Python's built-in compiler
- `ast.parse` - Abstract syntax tree parser
- Actually running the code

---

## Recommended Code Quality Process

### Step 1: Syntax Check (ALWAYS DO THIS FIRST)

```bash
# Check specific files
python3 tools/utils/check_syntax.py app/main.py app/services/scraped_topology_service.py

# Check entire directories
python3 tools/utils/check_syntax.py app/ tests/ tools/

# Verbose output
python3 tools/utils/check_syntax.py -v app/
```

**Why first?** Syntax errors prevent the code from running at all. No point in checking formatting or style if the code won't compile.

---

### Step 2: Format Code with Black

```bash
# Check formatting (doesn't modify files)
python3 -m black --check app/ tests/ tools/

# Auto-fix formatting
python3 -m black app/ tests/ tools/
```

**What it does**: Fixes indentation, spacing, line length, etc.

**Limitations**: Only fixes formatting, not syntax errors.

---

### Step 3: Lint with Flake8

```bash
# Check code style
python3 -m flake8 app/ tests/ tools/ --max-line-length=88 --ignore=E203,W503,E501
```

**What it does**: Checks for:
- PEP 8 violations
- Unused imports
- Undefined variables
- Code complexity issues

**Limitations**: Doesn't catch syntax errors or runtime errors.

---

### Step 4: Comprehensive Check (All-in-One)

```bash
# Run all checks in correct order
./scripts/check_code_quality.sh

# Check specific files/directories
./scripts/check_code_quality.sh app/main.py app/services/
```

**What it does**:
1. ✅ Syntax check (py_compile + ast.parse)
2. ✅ Black formatting check
3. ✅ Flake8 linting
4. ✅ Auto-fix formatting

---

## Quick Reference

### Before Committing Code

```bash
# 1. Check syntax (MOST IMPORTANT)
python3 tools/utils/check_syntax.py app/

# 2. Auto-format
python3 -m black app/

# 3. Check style
python3 -m flake8 app/ --max-line-length=88 --ignore=E203,W503,E501

# OR use the comprehensive script
./scripts/check_code_quality.sh app/
```

### When You Get Syntax Errors

1. **Run syntax checker** to find the exact error:
   ```bash
   python3 tools/utils/check_syntax.py path/to/file.py
   ```

2. **Look at the error message** - it shows:
   - Line number
   - Error type
   - Context around the error

3. **Fix the indentation/structure** - usually the issue

4. **Re-run syntax check** to verify:
   ```bash
   python3 tools/utils/check_syntax.py path/to/file.py
   ```

---

## Common Syntax Errors

### 1. Indentation Errors
```python
# ❌ Wrong
if condition:
    do_something()
        do_another_thing()  # Too much indentation

# ✅ Correct
if condition:
    do_something()
    do_another_thing()
```

### 2. Missing Colons
```python
# ❌ Wrong
if condition
    do_something()

# ✅ Correct
if condition:
    do_something()
```

### 3. Unmatched Brackets/Parentheses
```python
# ❌ Wrong
data = {"key": "value"  # Missing closing brace

# ✅ Correct
data = {"key": "value"}
```

### 4. Incorrect Try/Except Structure
```python
# ❌ Wrong
try:
    do_something()
    # Missing except or finally

# ✅ Correct
try:
    do_something()
except Exception as e:
    handle_error(e)
```

---

## Tools Comparison

| Tool | What It Checks | Catches Syntax Errors? |
|------|---------------|------------------------|
| `py_compile` | Syntax | ✅ **YES** |
| `ast.parse` | Syntax | ✅ **YES** |
| `black` | Formatting | ❌ No |
| `flake8` | Style | ❌ No |
| `mypy` | Types | ❌ No |
| `pylint` | Style + some syntax | ⚠️ Sometimes |

---

## Integration with AGENTS.md

The `AGENTS.md` file requires running code quality checks in this order:

1. **Black** (formatting)
2. **Flake8** (linting)
3. **py_compile** (syntax)

**However**, we recommend running syntax check **FIRST** because:
- Syntax errors prevent code from running
- No point formatting broken code
- Faster feedback loop

---

## Automated Checks

### Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Run syntax check before commit
python3 tools/utils/check_syntax.py app/ tests/ tools/
if [ $? -ne 0 ]; then
    echo "❌ Syntax errors found. Commit aborted."
    exit 1
fi
```

### CI/CD Integration

Add to your CI/CD pipeline:

```yaml
- name: Check Syntax
  run: python3 tools/utils/check_syntax.py app/ tests/ tools/

- name: Format Code
  run: python3 -m black --check app/ tests/ tools/

- name: Lint Code
  run: python3 -m flake8 app/ tests/ tools/ --max-line-length=88 --ignore=E203,W503,E501
```

---

## Summary

**Key Takeaway**: Always run syntax check **FIRST** before formatting or linting.

**Recommended Workflow**:
1. ✅ Syntax check (`check_syntax.py`)
2. ✅ Format code (`black`)
3. ✅ Lint code (`flake8`)
4. ✅ Test code (run it!)

**Or use the all-in-one script**:
```bash
./scripts/check_code_quality.sh
```
