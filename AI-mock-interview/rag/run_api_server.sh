#!/bin/bash

# Activate virtual environment if needed
# source /path/to/your/venv/bin/activate

# Set environment variables (if not using .env file)
# export GROQ_API_KEY="your-groq-api-key"
# export PINECONE_API_KEY="your-pinecone-api-key"
# export OPENAI_API_KEY="your-openai-api-key"

# Run the FastAPI server
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload 