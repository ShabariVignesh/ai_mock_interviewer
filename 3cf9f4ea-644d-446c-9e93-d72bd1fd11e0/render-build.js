import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Create dist directory if it doesn't exist
if (!fs.existsSync(path.join(__dirname, 'dist'))) {
  fs.mkdirSync(path.join(__dirname, 'dist'));
}

// Create a simple React app directly - no build needed
const htmlContent = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Mock Interview</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
      margin: 0;
      padding: 0;
      background-color: #f5f5f5;
      color: #333;
    }
    #root {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem;
    }
    .container {
      max-width: 800px;
      width: 100%;
      padding: 2rem;
      background-color: white;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    header {
      text-align: center;
      margin-bottom: 2rem;
    }
    h1 {
      color: #4f46e5;
      margin-bottom: 0.5rem;
    }
    p {
      margin-bottom: 1rem;
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
      margin: 0.5rem;
      cursor: pointer;
      border: none;
      transition: background-color 0.2s;
    }
    .button:hover {
      background-color: #4338ca;
    }
    .form-group {
      margin-bottom: 1rem;
    }
    label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
    }
    input, select, textarea {
      width: 100%;
      padding: 0.75rem;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 1rem;
    }
    .nav-links {
      display: flex;
      justify-content: center;
      margin-top: 2rem;
    }
  </style>
</head>
<body>
  <div id="root"></div>
  
  <script type="text/babel">
    // Simple React Router implementation
    const Route = ({ path, children }) => {
      const [currentPath, setCurrentPath] = React.useState(window.location.pathname);
      
      React.useEffect(() => {
        const onLocationChange = () => {
          setCurrentPath(window.location.pathname);
        };
        
        window.addEventListener('popstate', onLocationChange);
        
        return () => {
          window.removeEventListener('popstate', onLocationChange);
        };
      }, []);
      
      return currentPath === path ? children : null;
    };
    
    const Link = ({ to, children, className }) => {
      const handleClick = (e) => {
        e.preventDefault();
        window.history.pushState({}, '', to);
        window.dispatchEvent(new PopStateEvent('popstate'));
      };
      
      return (
        <a href={to} onClick={handleClick} className={className}>
          {children}
        </a>
      );
    };
    
    // Home Component
    const Home = () => {
      return (
        <div className="container">
          <header>
            <h1>AI Mock Interview</h1>
            <p>Practice your interview skills with AI-powered mock interviews</p>
          </header>
          
          <p>Welcome to the AI Mock Interview platform! This application provides realistic interview scenarios and valuable feedback to help you improve your interview performance.</p>
          
          <p>Get started by creating an account or logging in:</p>
          
          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
            <Link to="/login" className="button">Login</Link>
            <Link to="/register" className="button">Register</Link>
          </div>
          
          <div className="nav-links">
            <Link to="/api-docs" className="button">API Documentation</Link>
          </div>
        </div>
      );
    };
    
    // Login Component
    const Login = () => {
      return (
        <div className="container">
          <header>
            <h1>Login</h1>
            <p>Access your account</p>
          </header>
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input type="email" id="email" placeholder="Enter your email" />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input type="password" id="password" placeholder="Enter your password" />
          </div>
          
          <button className="button" style={{ width: '100%' }}>Login</button>
          
          <p style={{ textAlign: 'center', marginTop: '1rem' }}>
            Don't have an account? <Link to="/register">Register</Link>
          </p>
          
          <div className="nav-links">
            <Link to="/" className="button">Back to Home</Link>
          </div>
        </div>
      );
    };
    
    // Register Component
    const Register = () => {
      return (
        <div className="container">
          <header>
            <h1>Register</h1>
            <p>Create a new account</p>
          </header>
          
          <div className="form-group">
            <label htmlFor="name">Full Name</label>
            <input type="text" id="name" placeholder="Enter your full name" />
          </div>
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input type="email" id="email" placeholder="Enter your email" />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input type="password" id="password" placeholder="Enter your password" />
          </div>
          
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input type="password" id="confirmPassword" placeholder="Confirm your password" />
          </div>
          
          <button className="button" style={{ width: '100%' }}>Register</button>
          
          <p style={{ textAlign: 'center', marginTop: '1rem' }}>
            Already have an account? <Link to="/login">Login</Link>
          </p>
          
          <div className="nav-links">
            <Link to="/" className="button">Back to Home</Link>
          </div>
        </div>
      );
    };
    
    // API Docs Component
    const ApiDocs = () => {
      return (
        <div className="container">
          <header>
            <h1>API Documentation</h1>
          </header>
          
          <p>The API is available at: <a href="https://ai-interview-backend.onrender.com/docs" target="_blank" rel="noopener noreferrer">https://ai-interview-backend.onrender.com/docs</a></p>
          
          <div className="nav-links">
            <Link to="/" className="button">Back to Home</Link>
          </div>
        </div>
      );
    };
    
    // Main App Component
    const App = () => {
      return (
        <React.Fragment>
          <Route path="/">
            <Home />
          </Route>
          <Route path="/login">
            <Login />
          </Route>
          <Route path="/register">
            <Register />
          </Route>
          <Route path="/api-docs">
            <ApiDocs />
          </Route>
        </React.Fragment>
      );
    };
    
    // Render the App
    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
`;

// Write the HTML file to dist directory
fs.writeFileSync(path.join(__dirname, 'dist', 'index.html'), htmlContent);

console.log('Build completed successfully! Static files are in the dist directory.'); 