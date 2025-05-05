// API service for communicating with the backend
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Resume upload API
export const uploadResume = async (file: File, jobDescription: string, userId: number) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('job_description', jobDescription);
    formData.append('user_id', userId.toString());

    const response = await fetch(`${API_URL}/api/upload-resume`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to upload resume');
    }

    return await response.json();
  } catch (error) {
    console.error('Resume upload error:', error);
    throw error;
  }
};

// Start interview API
export const startInterview = async (
  userId: string,
  jobDescription: string,
  interviewType: string = 'technical',
  company?: string,
  role?: string,
  skill?: string,
  round?: string
): Promise<{ success: boolean, question?: string }> => {
  try {
    console.log(`API URL: ${API_URL}/api/start-interview`);
    
    // Create request payload
    const payload = {
      user_id: parseInt(userId),
      job_description: jobDescription,
      interview_type: interviewType
    };
    
    console.log('Sending interview data:', JSON.stringify(payload));
    
    // Make API call
    let response;
    try {
      response = await fetch(`${API_URL}/api/start-interview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      console.log('Response status:', response.status);
    } catch (fetchError) {
      console.error('Network error during fetch:', fetchError);
      console.log('Browser may be blocking the request due to CORS or network issues');
      throw new Error('Network error: Could not connect to the server');
    }
    
    // Handle non-success responses
    if (!response.ok) {
      let errorMessage = 'Failed to start interview';
      try {
        const errorData = await response.json();
        console.error('API error response:', errorData);
        errorMessage = errorData.detail || errorMessage;
      } catch (e) {
        console.error('Could not parse error response:', e);
      }
      throw new Error(errorMessage);
    }
    
    // Parse successful response
    let data;
    try {
      data = await response.json();
      console.log('Interview started successfully:', data);
    } catch (jsonError) {
      console.error('Error parsing JSON response:', jsonError);
      throw new Error('Invalid response from server');
    }
    
    // Return success with question if available
    return { 
      success: data.success || true,
      question: data.question || 'Hello! I\'ll be conducting your interview today. Could you start by telling me a bit about yourself and your background?'
    };
  } catch (error) {
    console.error('Error starting interview:', error);
    throw error;
  }
};

// Send message to chat API
export const sendChatMessage = async (message: string, userId: number) => {
  try {
    console.log(`Sending chat message to ${API_URL}/api/chat with user ID ${userId}`);
    
    const response = await fetch(`${API_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        user_id: userId,
      }),
    });

    console.log('Chat API response status:', response.status);
    
    if (!response.ok) {
      console.error('Error response status:', response.status);
      try {
        const errorData = await response.json();
        console.error('Error details:', errorData);
        throw new Error(errorData.detail || 'Failed to send message');
      } catch (parseError) {
        console.error('Error parsing error response:', parseError);
        throw new Error(`Failed to send message. Status code: ${response.status}`);
      }
    }

    const data = await response.json();
    console.log('Chat API response data:', data);
    return {
      response: data.response || "I'm having trouble understanding. Could you tell me more about your experience?",
      end_interview: data.end_interview || false
    };
  } catch (error) {
    console.error('Chat message error:', error);
    // Instead of throwing, return a fallback response
    return {
      response: "I'm having trouble understanding. Could you tell me more about your experience?",
      end_interview: false
    };
  }
};

// Update the response type to include abbreviated_interview
export interface ReportResponse {
  success: boolean;
  metrics: any;
  report: any;
  abbreviated_interview?: boolean;
}

// Generate interview report
export const generateReport = async (userId: string): Promise<ReportResponse> => {
  try {
    console.log(`Generating report for user ID: ${userId}`);
    
    const response = await fetch(`${API_URL}/api/generate-report`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
      }),
    });

    console.log('Report API response status:', response.status);
    
    if (!response.ok) {
      console.error('Report API error status:', response.status);
      const errorData = await response.json();
      console.error('Report API error details:', errorData);
      throw new Error(errorData.detail || 'Failed to generate report');
    }

    const data = await response.json();
    console.log('Report API response data:', data);
    return {
      success: true,
      metrics: data.metrics || {},
      report: data.report || {},
      abbreviated_interview: data.abbreviated_interview || false
    };
  } catch (error) {
    console.error('Report generation error:', error);
    throw error;
  }
}; 