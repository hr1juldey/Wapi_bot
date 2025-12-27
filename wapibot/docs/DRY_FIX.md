# DRY Violation Fix

**Date**: 2025-12-27
**Issue**: Duplicate LLM configuration
**Status**: ✅ **FIXED**

---

## Problem

Created `src/dspy_modules/lm_config.py` which duplicated functionality already present in `src/core/dspy_config.py`.

**Violation**:
- `dspy_config.py` already handles Ollama LLM initialization
- `lm_config.py` re-implemented the same Ollama configuration
- Both files creating `dspy.LM` instances for Ollama

---

## Solution

### 1. Removed Duplicate File
```bash
rm src/dspy_modules/lm_config.py
```

### 2. Extended Existing Configuration

**File**: `src/core/dspy_config.py`

**Added**:
- `model_override` parameter to `_get_ollama_lm()` method
- `use_teacher_lm()` context manager for GEPA optimization

**Before**:
```python
def _get_ollama_lm(self) -> dspy.LM:
    model_name = f"ollama_chat/{settings.ollama_model}"
    return dspy.LM(model=model_name, api_base=settings.ollama_base_url, ...)
```

**After**:
```python
def _get_ollama_lm(self, model_override: str = None) -> dspy.LM:
    model = model_override or settings.ollama_model
    model_name = f"ollama_chat/{model}"
    return dspy.LM(model=model_name, api_base=settings.ollama_base_url, ...)

@contextmanager
def use_teacher_lm(self, teacher_model: str = "qwen3:8b"):
    """Context manager for GEPA teacher LLM."""
    with self.use_provider("ollama", model_override=teacher_model) as teacher_lm:
        yield teacher_lm
```

### 3. Updated GEPA Task

**File**: `src/tasks/gepa_optimization_task.py`

**Changed**:
```python
# OLD (using deleted lm_config.py)
from dspy_modules.lm_config import get_student_lm, get_teacher_context

student_lm = get_student_lm()
dspy.configure(lm=student_lm)

with get_teacher_context():
    optimizer = dspy.GEPA(...)

# NEW (using existing dspy_config.py)
from core.dspy_config import dspy_configurator

# Student LLM already configured via dspy_configurator.configure()

teacher_model = settings.gepa_teacher_model
with dspy_configurator.use_teacher_lm(teacher_model):
    optimizer = dspy.GEPA(...)
```

---

## Benefits of Fix

1. **Single Source of Truth**: Only `dspy_config.py` handles LLM configuration
2. **Reuses Existing Code**: Leverages existing multi-provider support
3. **Maintains Settings Integration**: Uses centralized `settings` object
4. **Cleaner Architecture**: One configurator, multiple contexts

---

## New Usage Pattern

### Teacher LLM for GEPA Optimization

```python
from core.dspy_config import dspy_configurator

# Use teacher LLM temporarily
with dspy_configurator.use_teacher_lm("qwen3:8b"):
    optimizer = dspy.GEPA(metric=metric)
    optimized = optimizer.compile(baseline, trainset=data)
# Automatically reverts to student LLM after context
```

### Override Any Model

```python
# Use different Ollama model temporarily
with dspy_configurator.use_provider("ollama", model_override="llama3.2"):
    result = module(...)
```

---

## Files Changed

**Deleted** (1):
- `src/dspy_modules/lm_config.py` ❌

**Modified** (2):
- `src/core/dspy_config.py` - Added `model_override` and `use_teacher_lm()`
- `src/tasks/gepa_optimization_task.py` - Updated imports and usage

**Remaining Implementation**: 14 new files (was 15)

---

## Validation

```bash
# Check syntax
python3 -m py_compile src/core/dspy_config.py
python3 -m py_compile src/tasks/gepa_optimization_task.py

# Verify no remaining imports
grep -r "from dspy_modules.lm_config import" src/
# Should return nothing

# Test dual LLM setup
python3 -c "
from src.core.dspy_config import dspy_configurator

# Configure student LLM
dspy_configurator.configure()

# Test teacher context
with dspy_configurator.use_teacher_lm('qwen3:8b'):
    print('✅ Teacher LLM context working')
"
```

---

## DRY Principle Restored

✅ **No duplication**: Single LLM configuration class
✅ **Reusable**: Context managers for different models
✅ **Maintainable**: Changes in one place affect all usage
✅ **Extensible**: Easy to add new providers or models

**Status**: DRY violation fixed, architecture improved.
