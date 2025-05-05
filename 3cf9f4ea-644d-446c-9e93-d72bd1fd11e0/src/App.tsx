import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from './context/AuthContext';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Home } from './pages/Home';
import { InterviewSetup } from './pages/InterviewSetup';
import { ResumeUpload } from './pages/ResumeUpload';
import { Interview } from './pages/Interview';
import { Feedback } from './pages/Feedback';
export function App() {
  return <Router>
      <AuthProvider>
        <Toaster position="top-center" />
        <Layout>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<Home />} />
            <Route path="/setup" element={<InterviewSetup />} />
            <Route path="/resume-upload" element={<ResumeUpload />} />
            <Route path="/interview" element={<Interview />} />
            <Route path="/feedback" element={<Feedback />} />
          </Routes>
        </Layout>
      </AuthProvider>
    </Router>;
}