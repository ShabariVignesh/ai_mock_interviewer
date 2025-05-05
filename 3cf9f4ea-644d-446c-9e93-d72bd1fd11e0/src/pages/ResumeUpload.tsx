import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileTextIcon, CheckCircleIcon } from 'lucide-react';
import { toast } from 'sonner';
export function ResumeUpload() {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [parsedContent, setParsedContent] = useState('');
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setUploading(true);
      // Simulate file upload and parsing
      await new Promise(resolve => setTimeout(resolve, 2000));
      setParsedContent('Your resume has been successfully parsed...');
      setUploading(false);
      setUploaded(true);
    }
  };
  return <div className="max-w-3xl mx-auto">
      <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl overflow-hidden transition-all animate-slide-up">
        <div className="p-8 bg-gradient-to-r from-sjsu-blue to-blue-600 text-white">
          <h1 className="text-3xl font-bold">Upload Your Resume</h1>
          <p className="mt-2 text-blue-100">
            We'll analyze your resume to personalize your interview experience
          </p>
        </div>
        <div className="p-8 space-y-6">
          <div className={`relative transition-all duration-300 ${uploaded ? 'opacity-50' : ''}`}>
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 transition-all hover:border-sjsu-blue">
              <input type="file" onChange={handleFileUpload} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" accept=".pdf,.doc,.docx" disabled={uploaded} />
              <div className="text-center">
                <Upload className={`mx-auto h-12 w-12 ${uploading ? 'animate-bounce' : ''} ${uploaded ? 'text-green-500' : 'text-gray-400'}`} />
                <p className="mt-4 text-sm text-gray-600">
                  Drag and drop your resume here, or click to browse
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  PDF, DOC up to 10MB
                </p>
              </div>
            </div>
          </div>
          {uploaded && <div className="bg-green-50 border border-green-100 rounded-xl p-6 animate-fade-in">
              <div className="flex items-center space-x-3">
                <CheckCircleIcon className="w-6 h-6 text-green-500" />
                <span className="text-green-700 font-medium">
                  Resume uploaded successfully!
                </span>
              </div>
              <div className="mt-4 text-sm text-gray-600">{parsedContent}</div>
            </div>}
          <div className="flex justify-end space-x-4">
            <button type="button" onClick={() => navigate('/setup')} className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors">
              Back
            </button>
            <button onClick={() => navigate('/interview')} disabled={!uploaded} className={`px-6 py-2 text-sm font-medium text-white rounded-lg transition-all
                ${uploaded ? 'bg-gradient-to-r from-sjsu-blue to-blue-600 hover:from-blue-600 hover:to-sjsu-blue' : 'bg-gray-300 cursor-not-allowed'}`}>
              Continue
            </button>
          </div>
        </div>
      </div>
    </div>;
}