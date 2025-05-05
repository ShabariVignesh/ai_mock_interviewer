# Deploying to Render

This guide provides instructions for deploying the AI Mock Interview application to Render.

## Prerequisites

1. A [Render](https://render.com) account
2. Your API keys:
   - GROQ API key
   - Pinecone API key (if applicable)
   - OpenAI API key (if applicable)

## Deployment Steps

### 1. Fork or Clone the Repository

Make sure you have a copy of this repository in your GitHub account.

### 2. Set Up the Blueprint

1. Log in to your Render dashboard
2. Go to **Blueprints** in the navigation menu
3. Click **New Blueprint Instance**
4. Connect your GitHub account if not already connected
5. Select your repository
6. Click **Connect**

Render will automatically detect the `render.yaml` file and set up both services (backend and frontend).

### 3. Configure Environment Variables

After the services are created, you'll need to set up your environment variables:

1. Go to the **ai-interview-backend** service
2. Navigate to the **Environment** tab
3. Add your API keys:
   - GROQ_API_KEY
   - PINECONE_API_KEY (if applicable)
   - OPENAI_API_KEY (if applicable)
4. Click **Save Changes**

### 4. Verify Deployment

1. Once both services are deployed, check the backend by visiting:
   `https://ai-interview-backend.onrender.com/docs`
   
2. You should see the FastAPI documentation page.

3. Check the frontend by visiting:
   `https://ai-interview-frontend.onrender.com`
   
4. You should see the AI Mock Interview application.

## Troubleshooting

### Backend Issues

- Check the logs in the Render dashboard for any errors
- Verify that your API keys are correctly set
- Ensure the backend service is in the "Live" state

### Frontend Issues

- Check if the frontend can connect to the backend API
- Verify that the `VITE_API_URL` environment variable is set correctly
- If CORS issues occur, you may need to update the backend to allow the frontend domain

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Deploying a Full-Stack App to Render](https://render.com/docs/deploy-fullstack-app) 