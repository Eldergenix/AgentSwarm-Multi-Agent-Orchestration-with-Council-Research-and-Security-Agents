# Sources and API Notes

The project was wired against current official OpenAI API documentation.

## OpenAI API quickstart

The official OpenAI API quickstart shows the Responses API with Python:

```python
from openai import OpenAI
client = OpenAI()
response = client.responses.create(
    model="gpt-5.5",
    input="Write a short bedtime story about a unicorn."
)
print(response.output_text)
```

Source: https://developers.openai.com/api/docs

## GPT-5.5 model page

The model page lists `gpt-5.5`, the Responses endpoint, structured output support, and pricing/context information.

Source: https://developers.openai.com/api/docs/models/gpt-5.5

## Structured outputs

The structured output guide describes JSON Schema outputs through the Responses API `text.format` mechanism.

Source: https://developers.openai.com/api/docs/guides/structured-outputs

## Implementation note

The project defaults to offline mock mode. Live mode requires:

```bash
pip install -e .[live]
export OPENAI_API_KEY="..."
coa run --mode live --model gpt-5.5 "..."
```
