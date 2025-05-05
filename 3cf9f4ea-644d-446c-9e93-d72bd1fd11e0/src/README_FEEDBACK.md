# Candidate Feedback System

This document explains the feedback system for the AI Mock Interview application, which provides candidates with actionable feedback based on their interview performance.

## Overview

The feedback system transforms technical NLP metrics into user-friendly, actionable feedback that candidates can understand and apply to improve their interview skills.

## Key Components

### 1. Backend Metrics Calculation (`feedback_metrics_api.py`)

The backend calculates three primary NLP metrics:

- **F1 Score**: Measures accuracy by considering both precision and recall of the candidate's answers
- **ROUGE Score**: Evaluates the quality and comprehensiveness of responses
- **BLEU Score**: Measures how close the candidate's responses are to reference/ideal answers

These metrics are calculated by comparing the candidate's responses with "ground truth" answers for each interview question.

### 2. Metrics Transformer (`metricTransformer.ts`)

This service transforms the technical NLP metrics into user-friendly feedback:

- Converts raw technical scores (0-1) to percentages (0-100%)
- Maps metrics to intuitive categories (Technical Knowledge, Communication, Problem Solving)
- Generates qualitative feedback based on score thresholds
- Identifies strengths and areas for improvement
- Extracts example answers to highlight good practices and areas for growth
- Suggests relevant learning resources based on performance

### 3. Enhanced Feedback UI (`Feedback.tsx`)

The feedback page presents the transformed metrics in an intuitive, actionable format:

- Overall performance score
- Category-specific performance with color-coded indicators
- Strengths and areas for growth in user-friendly language
- Example answers with feedback and improvement suggestions
- Recommended learning resources to address specific weaknesses
- Expandable sections for detailed information

## How It Works

1. When a candidate completes an interview, the system:
   - Retrieves interview questions and candidate responses
   - Compares responses with ground truth answers
   - Calculates F1, ROUGE, and BLEU scores
   - Packages this data in a standardized format

2. The frontend then:
   - Receives the raw metrics from the API
   - Transforms them using `metricTransformer.ts`
   - Displays the transformed feedback in the UI

3. The candidate receives:
   - A clear overall performance score
   - Specific feedback on their technical knowledge, communication, and problem-solving skills
   - Concrete examples of strong answers and areas to improve
   - Actionable recommendations for improvement
   - Resources to help address specific weaknesses

## Benefits

- **Candidate-Friendly**: Presents technical metrics in ways candidates can understand
- **Actionable**: Provides specific improvement suggestions rather than just scores
- **Example-Based**: Includes concrete examples from the interview to illustrate feedback
- **Resource-Oriented**: Suggests relevant resources for continued learning
- **Visually Intuitive**: Uses color-coding and visual indicators to communicate performance levels

## Integration with Existing System

The feedback system integrates with the existing interview flow:
1. Candidate completes interview in the Interview component
2. Backend processes and stores interview data
3. API endpoint generates NLP metrics
4. Frontend transforms and displays feedback
5. Candidate reviews feedback and can choose to take another interview

## Future Enhancements

- Trend analysis for candidates who take multiple interviews
- More granular feedback categories based on job role/industry
- Personalized learning paths based on feedback
- Audio/video analysis for non-verbal communication feedback 