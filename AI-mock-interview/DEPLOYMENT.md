# Deploying AI Mock Interview to Fly.io

This guide walks you through deploying the AI Mock Interview application to Fly.io.

## Prerequisites

1. **Fly.io Account**: Sign up at [fly.io](https://fly.io)
2. **Fly CLI**: Install following [these instructions](https://fly.io/docs/hands-on/install-flyctl/)
3. **API Keys**:
   - GROQ API key
   - Pinecone API key (if using vector database features)
   - OpenAI API key (if using OpenAI models)

## Deployment Steps

### 1. Log in to Fly.io

```bash
fly auth login
```

### 2. Set up environment variables

Create a `.env` file from the template:

```bash
cp env.template .env
```

Edit the `.env` file and add your actual API keys.

### 3. Set secrets in Fly.io

```bash
# Set your API keys as secrets
fly secrets set GROQ_API_KEY=your_groq_api_key_here
fly secrets set PINECONE_API_KEY=your_pinecone_api_key_here
fly secrets set OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Deploy the application

```bash
# Launch the application (first time only)
fly launch

# For subsequent deployments
fly deploy
```

### 5. Verify deployment

```bash
fly open
```

This will open your application in a web browser.

## Scaling and Monitoring

- **Scaling**: `fly scale count 2` to run 2 instances
- **Logs**: `fly logs` to view application logs
- **Dashboard**: Visit [fly.io/apps](https://fly.io/apps) to monitor your application

## Troubleshooting

- **Deployment fails**: Check your `fly.toml` and ensure your Dockerfile is correct
- **Application crashes**: Run `fly logs` to see what's going wrong
- **Environment variables**: Verify secrets with `fly secrets list`

## Additional Resources

- [Fly.io Documentation](https://fly.io/docs/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/) 