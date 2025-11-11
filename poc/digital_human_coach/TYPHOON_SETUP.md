# 🌪️ Typhoon AI Integration Guide

This guide explains how to use **Typhoon AI** (OpenTyphoon) models with the Digital Human Coach application.

## 🎯 What is Typhoon?

**Typhoon** is an open-source Thai-focused Large Language Model developed by SCB 10X and partners. The `typhoon2-qwen2vl-7b-vision-instruct` model is a multimodal model that supports both text and vision tasks.

## 🔑 Getting Your API Key

1. **Visit OpenTyphoon Platform**

   - Go to: https://opentyphoon.ai/
   - Or API docs: https://opentyphoon.ai/api

2. **Sign Up / Log In**

   - Create an account or log in

3. **Generate API Key**

   - Navigate to API Keys section
   - Create a new API key
   - Copy the key (you won't see it again!)

4. **Add to .env File**
   ```bash
   TYPHOON_API_KEY=your_actual_api_key_here
   ```

## 🔧 Configuration

The `.env` file is already configured to use Typhoon:

```properties
# LLM Configuration
LLM_PROVIDER=typhoon
LLM_MODEL=typhoon2-qwen2vl-7b-vision-instruct
TYPHOON_API_KEY=your_typhoon_api_key_here
```

## ✅ Verify Setup

Run the test script to verify your Typhoon API connection:

```bash
python test_typhoon.py
```

Expected output:

```
Testing Typhoon API configuration...
LLM Provider: typhoon
LLM Model: typhoon2-qwen2vl-7b-vision-instruct
Typhoon API Key: sk-xxxxx...

Sending test request to Typhoon...

✅ SUCCESS! Typhoon Response:
[Response from Typhoon model]
```

## 🌟 Model Features

### typhoon2-qwen2vl-7b-vision-instruct

- **Type**: Multimodal (Text + Vision)
- **Parameters**: 7B
- **Context Length**: Varies by version
- **Strengths**:
  - Strong Thai language understanding
  - English proficiency
  - Vision capabilities (image understanding)
  - Instruction following

## 🚀 Usage in Application

Once configured, Typhoon will be used for:

### 1. Conversation Mode

- Real-time coaching responses
- Context-aware dialogue
- Personalized communication tips

### 2. Evaluation Mode

- Video transcript analysis
- Comprehensive feedback generation
- Speech metrics interpretation
- Body language assessment

## 🔄 Switching Between Models

To switch back to other models, update `.env`:

### Use Google Gemini:

```properties
LLM_PROVIDER=google
LLM_MODEL=gemini-2.0-flash-exp
```

### Use OpenAI:

```properties
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
```

### Use Anthropic Claude:

```properties
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
```

Then restart the backend server.

## 💡 Tips & Best Practices

1. **API Rate Limits**: Be aware of your plan's rate limits
2. **Cost Monitoring**: Track your API usage regularly
3. **Error Handling**: The app will log detailed errors if API calls fail
4. **Fallback Options**: Consider having backup API keys for other providers

## 🐛 Troubleshooting

### Issue: "API Key not set"

**Solution**: Update `TYPHOON_API_KEY` in `.env` with your actual key

### Issue: "401 Unauthorized"

**Solution**: Verify your API key is valid and not expired

### Issue: "429 Rate Limit"

**Solution**: Wait a moment before retrying, or upgrade your plan

### Issue: "Model not found"

**Solution**: Verify the model name is exactly: `typhoon2-qwen2vl-7b-vision-instruct`

## 📚 Additional Resources

- **Typhoon Documentation**: https://opentyphoon.ai/docs
- **API Reference**: https://opentyphoon.ai/api
- **GitHub**: https://github.com/scb-10x
- **Model Card**: Check OpenTyphoon website for latest model details

## 🔐 Security Notes

- **Never commit** your API key to version control
- Store keys in `.env` file (already in `.gitignore`)
- Rotate keys periodically
- Use different keys for development and production

## 🎓 Example Prompts

The app uses these system prompts with Typhoon:

**Conversation Mode:**

```
You are an AI communication coach helping users improve their speaking skills.
Be encouraging, constructive, and engaging...
```

**Evaluation Mode:**

```
You are an expert communication evaluator. Analyze the provided transcript
and metrics to give constructive feedback...
```

These are optimized to work well with Typhoon's instruction-following capabilities.

---

**Note**: This integration uses Typhoon's OpenAI-compatible API endpoint, making it easy to switch between different LLM providers without changing your application code.
