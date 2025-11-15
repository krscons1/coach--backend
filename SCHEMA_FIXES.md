# Schema Forward Reference Fixes

## Issue

Pydantic v2 requires proper handling of forward references. The error was:
```
pydantic.errors.PydanticUndefinedAnnotation: name 'HabitStatsResponse' is not defined
```

## Solution

### 1. Added `from __future__ import annotations`

This makes all type annotations strings by default, allowing forward references to work properly.

**Files updated:**
- `app/schemas/entry.py`
- `app/schemas/prediction.py`
- `app/schemas/reports.py`

### 2. Reordered Class Definitions

In `entry.py`, moved `HabitStatsResponse` before `CheckInResponse` so it's defined when referenced.

### 3. Removed String Quotes from Return Types

Changed:
```python
def from_probability(cls, prob_maintain: float, **kwargs) -> "PredictionResponse":
```

To:
```python
def from_probability(cls, prob_maintain: float, **kwargs) -> PredictionResponse:
```

## Verification

The app now imports and starts successfully:
```bash
python -c "from app.main import app; print('✅ App starts successfully!')"
```

## Best Practices

For Pydantic v2:
1. Always use `from __future__ import annotations` at the top of schema files
2. Define classes before they're referenced when possible
3. Avoid string quotes in type annotations when using `__future__ annotations`

