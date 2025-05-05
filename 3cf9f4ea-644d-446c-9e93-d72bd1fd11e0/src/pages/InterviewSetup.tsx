import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, BriefcaseIcon, BuildingIcon, LayersIcon } from 'lucide-react';
import { toast } from 'sonner';
export function InterviewSetup() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    jobTitle: '',
    company: '',
    round: '',
    jobDescription: ''
  });
  const [resume, setResume] = useState<File | null>(null);
  const [parsedResume, setParsedResume] = useState('');
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setResume(file);
      // Simulate resume parsing
      const reader = new FileReader();
      reader.onload = e => {
        setParsedResume('Your resume content will appear here after processing...');
      };
      reader.readAsText(file);
    }
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resume) {
      toast.error('Please upload your resume');
      return;
    }
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      navigate('/interview');
    }, 2000);
  };
  return <div className="max-w-3xl mx-auto py-8">
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-6 bg-blue-50 border-b border-blue-100">
          <h1 className="text-2xl font-bold text-gray-900">
            Setup Your Interview
          </h1>
          <p className="mt-2 text-gray-600">
            Please provide details about the position you're interviewing for
          </p>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Job Title
              </label>
              <div className="mt-1 relative">
                <BriefcaseIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                <input type="text" required value={formData.jobTitle} onChange={e => setFormData({
                ...formData,
                jobTitle: e.target.value
              })} className="pl-10 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" placeholder="e.g. Frontend Developer" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Company Name
              </label>
              <div className="mt-1 relative">
                <BuildingIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                <input type="text" required value={formData.company} onChange={e => setFormData({
                ...formData,
                company: e.target.value
              })} className="pl-10 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" placeholder="e.g. Google" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Interview Round
              </label>
              <div className="mt-1 relative">
                <LayersIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
                <select required value={formData.round} onChange={e => setFormData({
                ...formData,
                round: e.target.value
              })} className="pl-10 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500">
                  <option value="">Select Round</option>
                  <option value="screening">Initial Screening</option>
                  <option value="technical">Technical Round</option>
                  <option value="system">System Design</option>
                  <option value="behavioral">Behavioral</option>
                  <option value="final">Final Round</option>
                </select>
              </div>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Job Description
            </label>
            <textarea required value={formData.jobDescription} onChange={e => setFormData({
            ...formData,
            jobDescription: e.target.value
          })} rows={4} className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" placeholder="Paste the job description here..." />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Upload Resume
            </label>
            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
              <div className="space-y-1 text-center">
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <div className="flex text-sm text-gray-600">
                  <label className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500">
                    <span>Upload a file</span>
                    <input type="file" className="sr-only" accept=".pdf,.doc,.docx" onChange={handleFileUpload} />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-xs text-gray-500">PDF, DOC up to 10MB</p>
              </div>
            </div>
          </div>
          {parsedResume && <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">
                Parsed Resume Content
              </label>
              <div className="mt-1 p-4 bg-gray-50 rounded-md">
                <p className="text-sm text-gray-600">{parsedResume}</p>
              </div>
            </div>}
          <div className="flex items-center justify-end space-x-4">
            <button type="button" onClick={() => navigate('/')} className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
              Cancel
            </button>
            <button type="submit" disabled={loading} className={`px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${loading ? 'opacity-75 cursor-not-allowed' : ''}`}>
              {loading ? 'Preparing Interview...' : 'Start Interview'}
            </button>
          </div>
        </form>
      </div>
    </div>;
}