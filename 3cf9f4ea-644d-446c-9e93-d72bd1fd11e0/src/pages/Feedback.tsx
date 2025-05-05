import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircleIcon, AlertCircleIcon, RefreshCwIcon, HomeIcon } from 'lucide-react';
export function Feedback() {
  const navigate = useNavigate();
  const feedbackData = {
    overallScore: 85,
    categories: [{
      name: 'Technical Knowledge',
      score: 90,
      feedback: 'Strong understanding of core concepts. Could improve on system design explanations.'
    }, {
      name: 'Communication',
      score: 85,
      feedback: 'Clear and concise responses. Consider providing more concrete examples.'
    }, {
      name: 'Problem Solving',
      score: 80,
      feedback: 'Good approach to breaking down problems. Work on optimizing solutions.'
    }],
    strengths: ['Clear communication style', 'Strong technical fundamentals', 'Good problem-solving approach'],
    improvements: ['Provide more specific examples', 'Elaborate on system design concepts', 'Work on solution optimization']
  };
  return <div className="max-w-4xl mx-auto py-8">
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="p-6 bg-blue-50 border-b border-blue-100">
          <h1 className="text-2xl font-bold text-gray-900">
            Interview Feedback
          </h1>
          <p className="mt-2 text-gray-600">
            Here's your detailed interview performance analysis
          </p>
        </div>
        <div className="p-6 space-y-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-blue-100">
              <span className="text-3xl font-bold text-blue-600">
                {feedbackData.overallScore}%
              </span>
            </div>
            <h2 className="mt-2 text-xl font-semibold text-gray-900">
              Overall Performance
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {feedbackData.categories.map((category, index) => <div key={index} className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900">{category.name}</h3>
                <div className="mt-2 h-2 bg-gray-200 rounded">
                  <div className="h-2 bg-blue-600 rounded" style={{
                width: `${category.score}%`
              }} />
                </div>
                <p className="mt-2 text-sm text-gray-600">
                  {category.feedback}
                </p>
              </div>)}
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <h3 className="flex items-center text-green-600 font-semibold mb-2">
                <CheckCircleIcon className="w-5 h-5 mr-2" />
                Strengths
              </h3>
              <ul className="space-y-2">
                {feedbackData.strengths.map((strength, index) => <li key={index} className="text-sm text-gray-600">
                    • {strength}
                  </li>)}
              </ul>
            </div>
            <div>
              <h3 className="flex items-center text-amber-600 font-semibold mb-2">
                <AlertCircleIcon className="w-5 h-5 mr-2" />
                Areas for Improvement
              </h3>
              <ul className="space-y-2">
                {feedbackData.improvements.map((improvement, index) => <li key={index} className="text-sm text-gray-600">
                    • {improvement}
                  </li>)}
              </ul>
            </div>
          </div>
          <div className="flex justify-center space-x-4">
            <button onClick={() => navigate('/setup')} className="flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700">
              <RefreshCwIcon className="w-4 h-4 mr-2" />
              Take Another Interview
            </button>
            <button onClick={() => navigate('/')} className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">
              <HomeIcon className="w-4 h-4 mr-2" />
              Return Home
            </button>
          </div>
        </div>
      </div>
    </div>;
}