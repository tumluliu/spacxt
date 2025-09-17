# LLM-Powered Natural Language Commands

SpacXT now supports advanced natural language processing powered by Large Language Models via OpenRouter. This enables much more flexible and intelligent spatial command understanding.

## Setup Instructions

### 1. Get OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Create an account and get your API key
3. Choose from models like Claude, GPT-4, Llama, etc.

### 2. Configure Environment

Create or update your `.env` file in the project root:

```bash
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_actual_api_key_here

# Optional: Specify model (defaults to GPT-4o-mini)
OPENROUTER_MODEL=openai/gpt-4o-mini
```

**Available Models:**
- `openai/gpt-4o-mini` (fast, cost-effective, recommended)
- `anthropic/claude-3-haiku-20240307` (fast alternative)
- `anthropic/claude-3-sonnet-20240229` (balanced)
- `openai/gpt-4o` (OpenAI's most capable)
- `meta-llama/llama-3.1-8b-instruct` (open source)

### 3. Test the Setup

Run the GUI demo:

```bash
cd examples
poetry run python demo_gui.py
```

If the API key is missing, the system will gracefully fall back to rule-based parsing with a warning.

## Enhanced Capabilities

### 🧠 **Intelligent Command Understanding**

The LLM can understand complex, natural commands:

**Simple Commands:**
- "put a coffee cup on the table"
- "add a book near the chair"

**Complex Commands:**
- "place a delicate wine glass elegantly on the dining table"
- "add a modern laptop computer to the workspace area"
- "move that chair closer to the kitchen stove"
- "put a small potted plant beside the window"

**Contextual Understanding:**
- "add another cup" (understands "another" means similar to existing)
- "move the red chair" (can identify objects by properties)
- "remove all books from the table" (batch operations)

### 🎯 **Smart Object Properties**

The LLM automatically generates realistic properties for objects:

- **Physical dimensions** based on real-world knowledge
- **Material properties** (ceramic, metal, plastic, etc.)
- **Affordances** (what the object can do)
- **Weight and fragility** for physics simulation
- **Appropriate colors** and visual properties

### 🔄 **Fallback Mechanism**

If LLM is unavailable:
- System automatically falls back to rule-based parsing
- Basic commands still work
- No interruption to core functionality

## Command Examples

### Adding Objects
```
"put a coffee cup on the table"
"add a modern laptop to the scene"
"place a wine glass elegantly on the dining table"
"set a small potted plant beside the window"
```

### Moving Objects
```
"move the chair closer to the stove"
"shift that cup near the lamp"
"relocate the book to the shelf"
```

### Removing Objects
```
"remove the coffee cup"
"take away the laptop"
"delete that book from the scene"
```

### Complex Spatial Relations
```
"put the cup on top of the book"
"place the lamp beside the computer"
"move the chair away from the table"
"add a phone next to the laptop"
```

## Technical Details

### LLM Integration
- Uses OpenAI-compatible API via OpenRouter
- Structured JSON output for reliable parsing
- Context-aware parsing with scene information
- Automatic object property enhancement

### Error Handling
- Graceful fallback to rule-based parsing
- Clear error messages for API issues
- Retry mechanisms for transient failures
- Validation of LLM responses

### Performance
- Optimized prompts for fast response
- Caching of object properties
- Minimal API calls per command
- Efficient context building

## Troubleshooting

### API Key Issues
```
⚠️  LLM client initialization failed: OPENROUTER_API_KEY not found
   Falling back to rule-based parsing
```
**Solution:** Add your API key to `.env` file

### Network Issues
```
❌ LLM API error: Connection timeout
```
**Solution:** Check internet connection, try again

### Invalid Commands
```
❌ Could not understand command
```
**Solution:** Try rephrasing the command more clearly

### Model Selection
For better results with complex commands, use more capable models:
```bash
OPENROUTER_MODEL=anthropic/claude-3-sonnet-20240229
```

## Cost Considerations

- **Haiku**: ~$0.25 per 1M input tokens (very affordable)
- **GPT-4o-mini**: ~$0.15 per 1M input tokens (cheapest)
- **Sonnet**: ~$3 per 1M input tokens (higher quality)

Most spatial commands use ~100-200 tokens, making costs negligible for typical usage.

---

**Ready to experience intelligent spatial reasoning with natural language? Set up your API key and start commanding your 3D world!** 🚀
