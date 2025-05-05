import React from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { LogOutIcon, HomeIcon, UserIcon } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
export function Layout({
  children
}: {
  children: React.ReactNode;
}) {
  const {
    isAuthenticated,
    logout
  } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
  return <div className="min-h-screen bg-gradient-to-b from-gray-50 to-gray-100">
      <nav className="bg-white/70 backdrop-blur-md shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <Link to="/" className="flex items-center space-x-3">
                <img src="/San_Jose_State_Spartans_logo.png" alt="SJSU Logo" className="h-10 w-auto" />
                <div className="flex flex-col">
                  <span className="text-lg font-bold text-sjsu-blue">
                    AI Mock Interviewer
                  </span>
                  <span className="text-xs text-sjsu-darkBlue/70">
                    By SJSU, for SJSU
                  </span>
                </div>
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              {isAuthenticated ? <>
                  <button onClick={() => navigate('/')} className="flex items-center px-4 py-2 text-sjsu-blue hover:bg-sjsu-lightBlue rounded-lg transition-colors">
                    <HomeIcon className="w-5 h-5 mr-1" />
                    Home
                  </button>
                  <button onClick={() => {
                logout();
                navigate('/login');
              }} className="flex items-center px-4 py-2 text-white bg-sjsu-blue hover:bg-sjsu-darkBlue rounded-lg transition-colors">
                    <LogOutIcon className="w-5 h-5 mr-1" />
                    Logout
                  </button>
                </> : !isAuthPage && <div className="flex items-center space-x-3">
                    <button onClick={() => navigate('/login')} className="px-4 py-2 text-sjsu-blue hover:bg-sjsu-lightBlue rounded-lg transition-colors">
                      Login
                    </button>
                    <button onClick={() => navigate('/register')} className="px-4 py-2 text-white bg-sjsu-blue hover:bg-sjsu-darkBlue rounded-lg transition-colors">
                      Sign Up
                    </button>
                  </div>}
            </div>
          </div>
        </div>
      </nav>
      <div className="relative">
        <div className="absolute top-0 right-0 w-1/3 h-1/3 bg-sjsu-gold/10 rounded-full blur-3xl -z-10" />
        <div className="absolute bottom-0 left-0 w-1/3 h-1/3 bg-sjsu-blue/10 rounded-full blur-3xl -z-10" />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
          {children}
        </main>
      </div>
    </div>;
}