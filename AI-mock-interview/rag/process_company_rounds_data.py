#!/usr/bin/env python3
"""
Process company-specific interview questions with round information
and add them to Pinecone vector database.
"""

import pandas as pd
import os
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv
from pinecone import Pinecone
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from langchain.schema import Document

# Load environment variables
load_dotenv()

# Initialize Pinecone with new class-based approach
pc = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY")
)

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Constants
INDEX_NAME = os.getenv("PINECONE_INDEX")
NAMESPACE = "company_rounds_questions"
DATA_PATH = "../data/Final_cleaned_rounds_filled.csv"

def clean_dataframe(df):
    """Clean and prepare the dataframe."""
    # Drop rows with missing values in critical columns
    df = df.dropna(subset=['Question', 'Answer'])
    
    # Fill missing values with empty strings or appropriate defaults
    df['Company_name'] = df['Company_name'].fillna('General')
    df['Role'] = df['Role'].fillna('General')
    df['Skill'] = df['Skill'].fillna('General')
    df['Question_category'] = df['Question_category'].fillna('Technical')
    df['Round'] = df['Round'].fillna('1')
    
    # Convert round to string
    df['Round'] = df['Round'].astype(str)
    
    # Clean whitespace
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].str.strip()
    
    return df

def get_existing_ids(index):
    """Get existing document IDs in the index."""
    try:
        # Query with empty embedding to get all IDs
        query_response = index.query(
            namespace=NAMESPACE,
            vector=[0] * 1536,  # Dummy vector
            top_k=10000,
            include_metadata=False,
            include_values=False
        )
        return set(match['id'] for match in query_response['matches'])
    except Exception as e:
        print(f"Error retrieving existing IDs: {e}")
        return set()

def main():
    # Load the dataset
    print(f"Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    
    # Clean the dataframe
    df = clean_dataframe(df)
    print(f"Loaded {len(df)} records")
    
    # Get Pinecone index
    index = pc.Index(INDEX_NAME)
    
    # Get existing IDs to avoid duplicates
    existing_ids = get_existing_ids(index)
    print(f"Found {len(existing_ids)} existing records in the index")
    
    # Prepare documents
    documents = []
    for i, row in tqdm(df.iterrows(), total=len(df), desc="Processing records"):
        # Create a unique ID
        doc_id = f"company_round_{i}"
        
        if doc_id in existing_ids:
            continue
        
        # Create a document
        document = Document(
            page_content=f"Question: {row['Question']}\nAnswer: {row['Answer']}",
            metadata={
                "company": row['Company_name'],
                "role": row['Role'],
                "skill": row['Skill'],
                "category": row['Question_category'],
                "round": row['Round'],
                "question": row['Question'],
                "answer": row['Answer'],
                "type": "company_round_question"
            }
        )
        documents.append(document)
    
    # Process in batches
    batch_size = 100
    total_batches = (len(documents) + batch_size - 1) // batch_size
    
    print(f"Adding {len(documents)} new documents to Pinecone in {total_batches} batches...")
    
    for i in tqdm(range(0, len(documents), batch_size), desc="Uploading batches"):
        batch = documents[i:i+batch_size]
        
        if not batch:
            continue
        
        # Create embeddings and add to Pinecone
        LangchainPinecone.from_documents(
            batch, 
            embeddings, 
            index_name=INDEX_NAME,
            namespace=NAMESPACE
        )
        
        # Sleep to avoid rate limits
        time.sleep(1)
    
    print("All documents have been added to Pinecone!")

if __name__ == "__main__":
    main() 