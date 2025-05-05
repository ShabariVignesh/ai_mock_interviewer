import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Create dist directory if it doesn't exist
if (!fs.existsSync(path.join(__dirname, 'dist'))) {
  fs.mkdirSync(path.join(__dirname, 'dist'));
}

// Create a simple HTML file
const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Mock Interview</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      background-color: #f5f5f5;
      color: #333;
    }
    .container {
      max-width: 800px;
      padding: 2rem;
      text-align: center;
      background-color: white;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    h1 {
      color: #4f46e5;
      margin-bottom: 1rem;
    }
    p {
      margin-bottom: 1.5rem;
      line-height: 1.6;
    }
    .button {
      display: inline-block;
      background-color: #4f46e5;
      color: white;
      padding: 0.75rem 1.5rem;
      border-radius: 4px;
      text-decoration: none;
      font-weight: 500;
      transition: background-color 0.2s;
    }
    .button:hover {
      background-color: #4338ca;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>AI Mock Interview</h1>
    <p>
      Welcome to the AI Mock Interview platform. This frontend is connected to our AI-powered backend
      that provides realistic interview scenarios and feedback.
    </p>
    <p>
      The application is currently under development. This is a placeholder page deployed on Render.
    </p>
    <a href="https://ai-interview-backend.onrender.com/docs" class="button">Visit API Documentation</a>
  </div>
</body>
</html>
`;

// Write the HTML file to dist directory
fs.writeFileSync(path.join(__dirname, 'dist', 'index.html'), htmlContent);

console.log('Build completed successfully! Static files are in the dist directory.'); 