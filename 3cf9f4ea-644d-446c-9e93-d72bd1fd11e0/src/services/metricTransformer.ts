/**
 * Metrics Transformer Service
 * Converts technical NLP evaluation metrics into user-friendly feedback
 */

interface RawMetrics {
  f1Score?: number;
  rougeScore?: number;
  bleuScore?: number;
  questionAnswers?: Array<{
    question: string;
    userAnswer: string;
    idealAnswer: string;
    score: number;
  }>;
}

export interface TransformedFeedback {
  overallScore: number;
  categories: Array<{
    name: string;
    score: number;
    feedback: string;
  }>;
  strengths: string[];
  improvements: string[];
  examples: {
    strong: Array<{
      question: string;
      answer: string;
      reason: string;
    }>;
    needsImprovement: Array<{
      question: string;
      answer: string;
      betterApproach: string;
    }>;
  };
  resources: Array<{
    title: string;
    description: string;
    link?: string;
  }>;
}

/**
 * Calculate a weighted overall score from individual metrics
 */
function calculateOverallScore(metrics: RawMetrics): number {
  const weights = {
    f1: 0.4,
    rouge: 0.3,
    bleu: 0.3,
  };

  // Default values in case metrics are missing
  const f1 = metrics.f1Score || 0;
  const rouge = metrics.rougeScore || 0;
  const bleu = metrics.bleuScore || 0;

  // Calculate weighted score and convert to percentage (0-100)
  const score = Math.round((f1 * weights.f1 + rouge * weights.rouge + bleu * weights.bleu) * 100);
  
  // Ensure score stays within bounds
  return Math.min(Math.max(score, 0), 100);
}

/**
 * Generate category-specific scores and feedback
 */
function generateCategories(metrics: RawMetrics): TransformedFeedback['categories'] {
  const categories = [
    {
      name: 'Technical Knowledge',
      score: Math.round((metrics.f1Score || 0) * 100),
      feedback: generateTechnicalFeedback(metrics.f1Score || 0),
    },
    {
      name: 'Communication',
      score: Math.round((metrics.rougeScore || 0) * 100),
      feedback: generateCommunicationFeedback(metrics.rougeScore || 0),
    },
    {
      name: 'Problem Solving',
      score: Math.round((metrics.bleuScore || 0) * 100),
      feedback: generateProblemSolvingFeedback(metrics.bleuScore || 0),
    },
  ];

  return categories;
}

/**
 * Generate feedback for technical knowledge based on F1 score
 */
function generateTechnicalFeedback(f1Score: number): string {
  if (f1Score > 0.85) {
    return 'Excellent technical knowledge demonstrated. Key concepts explained accurately and comprehensively.';
  } else if (f1Score > 0.7) {
    return 'Strong understanding of core concepts. Consider deepening knowledge in advanced topics.';
  } else if (f1Score > 0.5) {
    return 'Adequate technical knowledge shown. Focus on explaining concepts more thoroughly and accurately.';
  } else {
    return 'Technical knowledge needs improvement. Consider studying fundamental concepts more deeply.';
  }
}

/**
 * Generate feedback for communication based on ROUGE score
 */
function generateCommunicationFeedback(rougeScore: number): string {
  if (rougeScore > 0.85) {
    return 'Excellent communication skills. Explanations were clear, concise, and well-structured.';
  } else if (rougeScore > 0.7) {
    return 'Good communication overall. Try providing more concrete examples to illustrate your points.';
  } else if (rougeScore > 0.5) {
    return 'Communication is adequate but could be improved with clearer structure and more precise language.';
  } else {
    return 'Focus on improving communication clarity. Structure your answers and use specific terminology.';
  }
}

/**
 * Generate feedback for problem solving based on BLEU score
 */
function generateProblemSolvingFeedback(bleuScore: number): string {
  if (bleuScore > 0.85) {
    return 'Excellent problem-solving approach with methodical thinking and optimal solutions.';
  } else if (bleuScore > 0.7) {
    return 'Good problem-solving skills demonstrated. Work on optimizing your solutions further.';
  } else if (bleuScore > 0.5) {
    return 'Adequate problem-solving shown. Focus on breaking down problems more systematically.';
  } else {
    return 'Problem-solving approach needs improvement. Practice analyzing problems step-by-step.';
  }
}

/**
 * Identify strengths based on metrics and question performances
 */
function identifyStrengths(metrics: RawMetrics): string[] {
  const strengths: string[] = [];
  
  // Add strengths based on high scores
  if ((metrics.f1Score || 0) > 0.8) {
    strengths.push('Strong engagement throughout the interview process');
  } else if ((metrics.f1Score || 0) > 0.7) {
    strengths.push('Good level of engagement during the interview');
  }
  
  if ((metrics.rougeScore || 0) > 0.8) {
    strengths.push('Excellent communication with thorough answers');
  } else if ((metrics.rougeScore || 0) > 0.7) {
    strengths.push('Clear and effective communication style');
  }
  
  if ((metrics.bleuScore || 0) > 0.8) {
    strengths.push('Demonstrated consistent quality in responses');
  } else if ((metrics.bleuScore || 0) > 0.7) {
    strengths.push('Good overall performance throughout the interview');
  }
  
  // Add strengths based on question answers
  const answers = metrics.questionAnswers || [];
  if (answers.length > 0) {
    // Check for longer answers
    const longAnswers = answers.filter(qa => qa.userAnswer.length > 100);
    if (longAnswers.length > 0) {
      strengths.push('Provided detailed responses to complex questions');
    }
    
    // Check for consistent answers
    if (answers.length >= 3) {
      strengths.push('Maintained consistent engagement throughout the interview');
    }
  }
  
  // Ensure we have at least some strengths
  if (strengths.length === 0) {
    strengths.push('Willingness to engage with the interview process');
    strengths.push('Attempting to provide structured responses');
  }
  
  // Remove duplicates
  return [...new Set(strengths)];
}

/**
 * Identify areas for improvement based on metrics
 */
function identifyImprovements(metrics: RawMetrics): string[] {
  const improvements: string[] = [];
  
  // Add improvement areas based on lower scores
  if ((metrics.f1Score || 0) < 0.7) {
    improvements.push('Consider providing more complete answers to demonstrate deeper knowledge');
  }
  
  if ((metrics.rougeScore || 0) < 0.7) {
    improvements.push('Try to elaborate more in your responses with specific examples');
  }
  
  if ((metrics.bleuScore || 0) < 0.7) {
    improvements.push('Focus on maintaining consistent quality across all your answers');
  }
  
  // Add improvements based on question answers
  const answers = metrics.questionAnswers || [];
  if (answers.length > 0) {
    // Check for shorter answers
    const shortAnswers = answers.filter(qa => qa.userAnswer.length < 50);
    if (shortAnswers.length > 0) {
      improvements.push('Expand on shorter answers to demonstrate deeper knowledge and experience');
    }
    
    // Check for answer count
    if (answers.length < 3) {
      improvements.push('Continue practicing with more mock interviews to build confidence');
    }
  }
  
  // Ensure we have at least some improvement suggestions
  if (improvements.length === 0) {
    improvements.push('Continue building depth in your responses with concrete examples');
    improvements.push('Practice explaining complex concepts in simple terms');
  }
  
  // Remove duplicates
  return [...new Set(improvements)];
}

/**
 * Extract example answers to highlight strengths and areas for improvement
 */
function extractExamples(metrics: RawMetrics): TransformedFeedback['examples'] {
  const examples = {
    strong: [],
    needsImprovement: []
  } as TransformedFeedback['examples'];
  
  // If we have question/answer data
  if (metrics.questionAnswers && metrics.questionAnswers.length > 0) {
    // Sort by score to find strongest and weakest answers
    const sortedQA = [...metrics.questionAnswers].sort((a, b) => b.score - a.score);
    
    // Get strongest examples (up to 2)
    const strongAnswers = sortedQA.slice(0, Math.min(2, sortedQA.length));
    examples.strong = strongAnswers.map(qa => ({
      question: qa.question,
      answer: qa.userAnswer,
      reason: `Your answer demonstrated clear understanding and effective communication.`
    }));
    
    // Get weakest examples (up to 2)
    const weakAnswers = sortedQA.slice(Math.max(sortedQA.length - 2, 0));
    examples.needsImprovement = weakAnswers.map(qa => ({
      question: qa.question,
      answer: qa.userAnswer,
      betterApproach: `Consider: "${qa.idealAnswer.substring(0, 100)}..."`
    }));
  }
  
  return examples;
}

/**
 * Suggest relevant learning resources based on performance
 */
function suggestResources(metrics: RawMetrics): TransformedFeedback['resources'] {
  const resources = [];
  
  // Suggest technical resources if technical score is low
  if ((metrics.f1Score || 0) < 0.7) {
    resources.push({
      title: 'Technical Foundations',
      description: 'Review core technical concepts to strengthen your fundamental knowledge.',
      link: 'https://www.codecademy.com/'
    });
  }
  
  // Suggest communication resources if communication score is low
  if ((metrics.rougeScore || 0) < 0.7) {
    resources.push({
      title: 'Technical Communication',
      description: 'Practice explaining technical concepts clearly and concisely.',
      link: 'https://www.toastmasters.org/'
    });
  }
  
  // Suggest problem-solving resources if problem-solving score is low
  if ((metrics.bleuScore || 0) < 0.7) {
    resources.push({
      title: 'Problem-Solving Techniques',
      description: 'Enhance your analytical thinking and problem decomposition skills.',
      link: 'https://leetcode.com/'
    });
  }
  
  // Always add interview preparation resource
  resources.push({
    title: 'Interview Preparation',
    description: 'Continue practicing with mock interviews to build confidence.',
    link: 'https://www.pramp.com/'
  });
  
  return resources;
}

/**
 * Main function to transform raw metrics into user-friendly feedback
 */
export function transformMetrics(rawMetrics: RawMetrics): TransformedFeedback {
  return {
    overallScore: calculateOverallScore(rawMetrics),
    categories: generateCategories(rawMetrics),
    strengths: identifyStrengths(rawMetrics),
    improvements: identifyImprovements(rawMetrics),
    examples: extractExamples(rawMetrics),
    resources: suggestResources(rawMetrics)
  };
}

/**
 * Generate mock metrics for testing when real metrics aren't available
 */
export function generateMockMetrics(): RawMetrics {
  return {
    f1Score: 0.75,
    rougeScore: 0.68,
    bleuScore: 0.72,
    questionAnswers: [
      {
        question: "Explain the concept of REST API.",
        userAnswer: "REST APIs use HTTP methods like GET, POST, PUT, DELETE to perform operations on resources identified by URLs.",
        idealAnswer: "REST (Representational State Transfer) is an architectural style for designing networked applications. REST APIs use HTTP methods (GET, POST, PUT, DELETE) to perform operations on resources identified by URLs. They're stateless, cacheable, and provide a uniform interface.",
        score: 0.78
      },
      {
        question: "What's the difference between let and var in JavaScript?",
        userAnswer: "let is block scoped and var is function scoped.",
        idealAnswer: "The key differences between let and var are: 1) let is block-scoped while var is function-scoped, 2) let variables cannot be redeclared in the same scope, 3) let variables are not hoisted to the top of their scope, and 4) let variables cannot be accessed before declaration (temporal dead zone).",
        score: 0.45
      }
    ]
  };
} 