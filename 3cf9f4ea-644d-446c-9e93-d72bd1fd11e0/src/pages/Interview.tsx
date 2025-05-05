import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { MicIcon, StopCircleIcon, KeyboardIcon, XIcon } from 'lucide-react';
interface Message {
  role: 'user' | 'ai';
  content: string;
}
export function Interview() {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([{
    role: 'ai',
    content: "Hello! I'm your AI interviewer today. Let's begin with a common question: Could you tell me about yourself and your background?"
  }]);
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [showKeyboard, setShowKeyboard] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth'
    });
  };
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  const handleSend = () => {
    if (!input.trim()) return;
    setMessages([...messages, {
      role: 'user',
      content: input
    }]);
    setInput('');
    setShowKeyboard(false);
    // Simulate AI response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        role: 'ai',
        content: 'Thank you for sharing that. Next question: What made you interested in this position and our company?'
      }]);
    }, 1000);
  };
  const toggleRecording = () => {
    setIsRecording(!isRecording);
    setShowKeyboard(false);
    // Implement actual voice recording logic here
  };
  return <div className="max-w-5xl mx-auto h-[85vh] relative">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-radial from-sjsu-blue/5 to-transparent -z-10" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-32 bg-sjsu-gold/10 rounded-full blur-3xl" />
      <div className="h-full flex flex-col bg-white/80 backdrop-blur-md rounded-2xl shadow-2xl overflow-hidden border border-white/20">
        <div className="p-6 bg-gradient-to-r from-sjsu-blue to-blue-600 text-white">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold">Interview Session</h1>
              <p className="text-sm text-blue-100">
                Frontend Developer Position
              </p>
            </div>
            <div className="flex space-x-3">
              <button onClick={() => navigate('/')} className="px-4 py-2 text-sm bg-white/10 hover:bg-white/20 rounded-lg backdrop-blur-sm transition-all">
                Exit
              </button>
              <button onClick={() => navigate('/feedback')} className="px-4 py-2 text-sm bg-white/20 hover:bg-white/30 rounded-lg backdrop-blur-sm transition-all">
                End Interview
              </button>
            </div>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((message, index) => <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
              <div className={`max-w-[80%] p-4 rounded-2xl shadow-md 
                  ${message.role === 'user' ? 'bg-gradient-to-r from-sjsu-blue to-blue-600 text-white ml-12' : 'bg-white border border-gray-100 text-gray-900 mr-12'}`}>
                {message.content}
              </div>
            </div>)}
          <div ref={messagesEndRef} />
        </div>
        <div className="p-6 bg-white/70 backdrop-blur-sm border-t border-gray-100">
          <div className="flex items-center justify-center space-x-4">
            <button onClick={toggleRecording} className={`flex items-center justify-center w-16 h-16 rounded-full transition-all transform hover:scale-105
                ${isRecording ? 'bg-red-500 text-white animate-pulse-slow' : 'bg-gradient-to-r from-sjsu-blue to-blue-600 text-white shadow-lg'}`}>
              {isRecording ? <StopCircleIcon className="w-8 h-8" /> : <MicIcon className="w-8 h-8" />}
            </button>
            <button onClick={() => setShowKeyboard(!showKeyboard)} className={`p-3 rounded-full transition-all
                ${showKeyboard ? 'bg-sjsu-blue text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
              <KeyboardIcon className="w-6 h-6" />
            </button>
          </div>
          {showKeyboard && <div className="mt-4 relative animate-slide-up">
              <input type="text" value={input} onChange={e => setInput(e.target.value)} onKeyPress={e => e.key === 'Enter' && handleSend()} placeholder="Type your response..." className="w-full px-6 py-4 bg-white rounded-xl border border-gray-200 shadow-md focus:outline-none focus:ring-2 focus:ring-sjsu-blue" autoFocus />
              <button onClick={handleSend} disabled={!input.trim()} className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-sjsu-blue text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                <KeyboardIcon className="w-5 h-5" />
              </button>
            </div>}
          {isRecording && <div className="mt-4 text-center animate-fade-in">
              <div className="inline-flex items-center px-4 py-2 bg-red-50 text-red-600 rounded-full">
                <span className="mr-2">Recording in progress</span>
                <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse" />
              </div>
            </div>}
        </div>
      </div>
    </div>;
}