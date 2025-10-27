# LLM Provider Configuration Guide

## Overview

Autobox Engine supports two LLM providers through the Vercel AI SDK:
1. **Ollama** - Local models running on your machine (default)
2. **OpenAI** - OpenAI proprietary cloud API (optional)

## Supported Providers

### 1. **Ollama (Local Models)** - Default ✅

Runs models locally on your machine at `localhost:11434`.

**Supported Models:**
- `gpt-oss:20b` - OpenAI-compatible OSS model
- `deepseek-r1:7b` - DeepSeek reasoning model (local)
- `llama2:latest` - Meta's Llama 2
- Any other model available in your local Ollama installation

**Configuration:**
```bash
LLM_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434/v1
```

**Usage:**
```json
// In your simulation config
{
  "workers": [
    {
      "name": "ANA",
      "llm": { "model": "deepseek-r1:7b" }
    }
  ]
}
```

---

### 2. **OpenAI (Cloud API)** - Optional

Use OpenAI's proprietary cloud models.

**Supported Models:**
- `gpt-4o` - Latest GPT-4 Omni
- `gpt-4o-mini` - Smaller, faster GPT-4 Omni
- `gpt-3.5-turbo` - GPT-3.5 Turbo
- Any official OpenAI model

**Configuration:**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-real-openai-api-key
# OPENAI_BASE_URL=https://api.openai.com/v1  # Optional
```

**Usage:**
```json
// In your simulation config
{
  "workers": [
    {
      "name": "ANA",
      "llm": { "model": "gpt-4o-mini" }
    }
  ]
}
```

---

## Quick Start

### Option 1: Running with Ollama (Default) ✅

1. **Install Ollama:**
   ```bash
   # macOS
   brew install ollama

   # Or download from https://ollama.com
   ```

2. **Pull models:**
   ```bash
   ollama pull gpt-oss:20b
   ollama pull deepseek-r1:7b
   ollama pull llama2:latest
   ```

3. **Start Ollama server:**
   ```bash
   ollama serve
   ```

4. **Configure `.env`:**
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_URL=http://localhost:11434/v1
   ```

5. **Run simulation:**
   ```bash
   yarn dev --simulation-name=gift_choice_2
   ```

---

### Option 2: Switching to OpenAI Cloud

1. **Update `.env`:**
   ```bash
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-real-openai-api-key
   ```

2. **Update simulation config (optional):**
   ```json
   {
     "workers": [
       {
         "name": "ANA",
         "llm": { "model": "gpt-4o-mini" }
       }
     ]
   }
   ```

3. **Run simulation:**
   ```bash
   yarn dev --simulation-name=gift_choice_2
   ```

---

## Important Notes

### 💡 Provider Comparison

| Feature | Ollama (Local) | OpenAI (Cloud) |
|---------|---------------|----------------|
| Cost | Free | Paid per token |
| Speed | Depends on hardware | Fast |
| Privacy | 100% local | Data sent to OpenAI |
| Models | gpt-oss:20b, deepseek-r1:7b, llama2 | gpt-4o, gpt-4o-mini, etc. |

### 🔧 Per-Agent Configuration

You can specify different models for different agents:

```json
{
  "planner": {
    "llm": { "model": "gpt-oss:20b" }
  },
  "workers": [
    {
      "name": "ANA",
      "llm": { "model": "deepseek-r1:7b" }
    },
    {
      "name": "JOHN",
      "llm": { "model": "llama2:latest" }
    }
  ]
}
```

**Note:** All agents use the same `LLM_PROVIDER` - you cannot mix Ollama and OpenAI in a single simulation.

---

## Troubleshooting

### Error: "Cannot connect to Ollama"
```bash
# Ensure Ollama is running:
ollama serve

# Verify models are available:
ollama list
```

### Error: "Invalid API key" (OpenAI)
```bash
# Verify your .env file:
echo $OPENAI_API_KEY

# Key should start with "sk-"
```

### Error: "Model not found"
```bash
# For Ollama: Pull the model first
ollama pull deepseek-r1:7b

# For OpenAI: Check model name is correct
# Valid: gpt-4o-mini, gpt-4o
# Invalid: gpt-5-nano (doesn't exist on OpenAI cloud)
```

---

## Architecture

Built with **Vercel AI SDK** (version 5), providing:
- ✅ Unified API for Ollama and OpenAI
- ✅ Type-safe model configuration
- ✅ Automatic streaming support
- ✅ Built-in error handling

See `src/core/llm/createAiProcessor.ts` for implementation.
