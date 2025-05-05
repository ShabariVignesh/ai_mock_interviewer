from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import nltk
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.bleu_score import SmoothingFunction
from rouge_score import rouge_scorer
from sklearn.metrics import f1_score
import numpy as np
from .database import get_user_interview_data

# Download required NLTK resources
try:
    nltk.download('punkt', quiet=True)
except:
    pass

router = APIRouter()

class ReportRequest(BaseModel):
    user_id: int

class QuestionAnswer(BaseModel):
    question: str
    userAnswer: str
    idealAnswer: str
    score: float

class Metrics(BaseModel):
    f1Score: float
    rougeScore: float
    bleuScore: float
    questionAnswers: List[QuestionAnswer]

class ReportResponse(BaseModel):
    success: bool
    metrics: Optional[Metrics] = None
    message: Optional[str] = None

def calculate_f1_score(user_answer: str, ideal_answer: str) -> float:
    """
    Calculate F1 score between user answer and ideal answer.
    Uses a simple token-based approach.
    """
    # Tokenize the answers
    user_tokens = set(nltk.word_tokenize(user_answer.lower()))
    ideal_tokens = set(nltk.word_tokenize(ideal_answer.lower()))
    
    # Calculate precision, recall, F1
    if len(user_tokens) == 0:
        return 0.0
    
    true_positives = len(user_tokens.intersection(ideal_tokens))
    precision = true_positives / len(user_tokens) if len(user_tokens) > 0 else 0
    recall = true_positives / len(ideal_tokens) if len(ideal_tokens) > 0 else 0
    
    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return float(f1)

def calculate_rouge_score(user_answer: str, ideal_answer: str) -> float:
    """
    Calculate ROUGE score for evaluating summary quality.
    """
    scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
    scores = scorer.score(ideal_answer, user_answer)
    
    # Average the different ROUGE metrics
    rouge_1 = scores['rouge1'].fmeasure
    rouge_2 = scores['rouge2'].fmeasure
    rouge_l = scores['rougeL'].fmeasure
    
    # Return average of ROUGE scores
    return float((rouge_1 + rouge_2 + rouge_l) / 3)

def calculate_bleu_score(user_answer: str, ideal_answer: str) -> float:
    """
    Calculate BLEU score for comparing machine translation to human reference.
    """
    # Tokenize the sentences
    reference = [nltk.word_tokenize(ideal_answer.lower())]
    hypothesis = nltk.word_tokenize(user_answer.lower())
    
    # Apply smoothing to handle cases with no n-gram overlaps
    smoothie = SmoothingFunction().method1
    
    # Calculate BLEU score
    try:
        bleu = sentence_bleu(reference, hypothesis, smoothing_function=smoothie)
        return float(bleu)
    except:
        return 0.0

def process_interview_data(data: List[Dict[str, Any]]) -> Metrics:
    """
    Process interview data to calculate metrics.
    """
    f1_scores = []
    rouge_scores = []
    bleu_scores = []
    question_answers = []
    
    for item in data:
        question = item.get('question', '')
        user_answer = item.get('answer', '')
        ideal_answer = item.get('ground_truth', '')
        
        if not question or not user_answer or not ideal_answer:
            continue
        
        # Calculate individual metrics
        f1 = calculate_f1_score(user_answer, ideal_answer)
        rouge = calculate_rouge_score(user_answer, ideal_answer)
        bleu = calculate_bleu_score(user_answer, ideal_answer)
        
        # Calculate overall score for this answer as weighted average
        score = 0.4 * f1 + 0.3 * rouge + 0.3 * bleu
        
        # Store all scores
        f1_scores.append(f1)
        rouge_scores.append(rouge)
        bleu_scores.append(bleu)
        
        # Add to question-answer pairs
        question_answers.append(
            QuestionAnswer(
                question=question,
                userAnswer=user_answer,
                idealAnswer=ideal_answer,
                score=score
            )
        )
    
    # Calculate average scores
    avg_f1 = np.mean(f1_scores) if f1_scores else 0.0
    avg_rouge = np.mean(rouge_scores) if rouge_scores else 0.0
    avg_bleu = np.mean(bleu_scores) if bleu_scores else 0.0
    
    return Metrics(
        f1Score=float(avg_f1),
        rougeScore=float(avg_rouge),
        bleuScore=float(avg_bleu),
        questionAnswers=question_answers
    )

@router.post("/api/generate-report", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Generate performance report for a user's interview.
    """
    try:
        # Get interview data from database
        interview_data = get_user_interview_data(request.user_id)
        
        if not interview_data:
            return ReportResponse(
                success=False,
                message="No interview data found for this user"
            )
        
        # Process interview data to calculate metrics
        metrics = process_interview_data(interview_data)
        
        return ReportResponse(
            success=True,
            metrics=metrics
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        ) 