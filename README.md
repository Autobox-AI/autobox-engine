# Autobox Engine

## Testing

Run tests using `uv` with pytest:

```bash
# Run all tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=autobox

# Run specific test file
uv run pytest tests/config/test_loader.py

# Run specific test function
uv run pytest tests/config/test_loader.py::test_loader

# Run tests matching a pattern
uv run pytest tests/ -k "loader"

# Run with detailed failure output
uv run pytest tests/ -vv

# Run and stop on first failure
uv run pytest tests/ -x
```