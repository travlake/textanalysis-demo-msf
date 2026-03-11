# Text Analysis Example

## API Configuration

- The `.env` file contains `ANTHROPIC_API_KEY` for direct Anthropic API access.
- The system has `ANTHROPIC_BASE_URL` set globally to Portkey (`https://api.portkey.ai`) for Claude Code usage.
- Scripts in this project must explicitly set `base_url='https://api.anthropic.com'` to bypass Portkey and use the direct API key:

```python
client = anthropic.Anthropic(
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    base_url='https://api.anthropic.com'
)
```
