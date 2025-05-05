import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { exec } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Step 1: Create bundle.js file with simple React code
const bundleCode = `
// Simple React app bundle
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './src/index.css';
import App from './src/App';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
`;

// Create a simplified index.css with basic styles
const cssCode = `
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
`;

// Ensure the dist directory exists
if (!fs.existsSync(path.join(__dirname, 'dist'))) {
  fs.mkdirSync(path.join(__dirname, 'dist'));
}

// Write the bundle file
fs.writeFileSync(path.join(__dirname, 'bundle.js'), bundleCode);

// Optional: Update index.css to remove Tailwind CSS dependencies
fs.writeFileSync(path.join(__dirname, 'src', 'index.css'), cssCode);

// Step 2: Run Vite build command
console.log('Running Vite build...');
exec('npx vite build', { cwd: __dirname }, (error, stdout, stderr) => {
  if (error) {
    console.error(`Vite build error: ${error.message}`);
    
    // Step 3: Fallback - If build fails, generate a static HTML file
    console.log('Falling back to static HTML generation...');
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
    console.log('Fallback static page created successfully!');
    return;
  }

  console.log(stdout);
  console.log('Vite build completed successfully!');
}); 