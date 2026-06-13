# GitMemory

GitMemory is a small learning project for exploring Git-like version control over LLM conversation context.

The goal is to understand how an LLM chat context can be saved, compared, rolled back, cleared, and restored.

This project is not a production-ready memory system. It is built step by step as a learning demo.

## What It Does

GitMemory manages an small LLM-style context list:

```python
[
  {"role": "user", "content": "hello"},
  {"role": "assistant", "content": "hi"}
]
