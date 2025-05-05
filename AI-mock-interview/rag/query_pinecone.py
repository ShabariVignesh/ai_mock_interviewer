import os
from pinecone import Pinecone
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Pinecone as LangchainPinecone
from dotenv import load_dotenv

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

INDEX_NAME = os.getenv("PINECONE_INDEX")
DEFAULT_NAMESPACE = "interview_questions"
COMPANY_ROUNDS_NAMESPACE = "company_rounds_questions"

def query_pinecone(query, top_k=5, namespace=DEFAULT_NAMESPACE, filters=None):
    """
    Query Pinecone for similar vectors.
    
    Args:
        query (str): The query string
        top_k (int): Number of results to return
        namespace (str): The namespace to query
        filters (dict): Optional filters to narrow down results
            Supports: company, role, skill, round
    
    Returns:
        dict: Query results
    """
    # Check if we should query company rounds data
    use_company_data = False
    if filters and any(key in filters for key in ['company', 'role', 'round']):
        use_company_data = True
        namespace = COMPANY_ROUNDS_NAMESPACE
    
    # Convert the query to an embedding
    query_embedding = embeddings.embed_query(query)
    
    # Get Pinecone index
    index = pc.Index(INDEX_NAME)
    
    # Prepare filter dict for Pinecone
    filter_dict = {}
    if filters:
        for key, value in filters.items():
            if value and value.lower() != 'any':
                filter_dict[key] = {"$eq": value}
    
    # Execute the query
    results = index.query(
        namespace=namespace,
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter_dict if filter_dict else None
    )
    
    # If no results and we're using company data, try with general namespace
    if not results['matches'] and use_company_data:
        print("No matches found in company data, trying general questions...")
        results = index.query(
            namespace=DEFAULT_NAMESPACE,
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
    
    return results

def retrieve_relevant_qa(query, top_k=3, company=None, role=None, skill=None, round=None):
    """
    Retrieve relevant Q&A pairs based on the query and optional filters.
    
    Args:
        query (str): The query string
        top_k (int): Number of results to return
        company (str): Filter by company
        role (str): Filter by role
        skill (str): Filter by skill/technology
        round (str): Filter by interview round
    
    Returns:
        list: List of relevant Q&A pairs
    """
    # Prepare filters
    filters = {}
    if company:
        filters['company'] = company
    if role:
        filters['role'] = role
    if skill:
        filters['skill'] = skill
    if round:
        filters['round'] = str(round)
    
    # Query the vector store
    results = query_pinecone(query, top_k=top_k, filters=filters)
    
    # Extract Q&A pairs with validation
    qa_pairs = []
    for match in results['matches']:
        metadata = match.get('metadata', {})
        if not metadata:
            continue
            
        # Ensure we never have None in question field
        question = metadata.get('question')
        if question is None:
            question = ''
            
        qa_pairs.append({
            'question': question,
            'answer': metadata.get('answer', ''),
            'score': match['score'],
            'company': metadata.get('company', 'General'),
            'role': metadata.get('role', 'General'),
            'skill': metadata.get('skill', 'General'),
            'round': metadata.get('round', '1')
        })
    
    return qa_pairs

if __name__ == "__main__":
    # Example usage
    query = "What is a binary search tree?"
    
    # General query
    print("General query:")
    results = retrieve_relevant_qa(query)
    for i, result in enumerate(results):
        print(f"{i+1}. Q: {result['question']}")
        print(f"   A: {result['answer']}")
        print(f"   Score: {result['score']:.4f}")
        print("---")
    
    # Company-specific query
    print("\nGoogle query for round 2:")
    results = retrieve_relevant_qa(query, company="Google", round="2")
    for i, result in enumerate(results):
        print(f"{i+1}. Q: {result['question']}")
        print(f"   A: {result['answer']}")
        print(f"   Company: {result['company']}")
        print(f"   Role: {result['role']}")
        print(f"   Round: {result['round']}")
        print(f"   Score: {result['score']:.4f}")
        print("---")

        print(f"{i+1}. Q: {result['question']}")
        print(f"   A: {result['answer']}")
        print(f"   Company: {result['company']}")
        print(f"   Role: {result['role']}")
        print(f"   Round: {result['round']}")
        print(f"   Score: {result['score']:.4f}")
        print("---")

        print(f"{i+1}. Q: {result['question']}")
        print(f"   A: {result['answer']}")
        print(f"   Company: {result['company']}")
        print(f"   Role: {result['role']}")
        print(f"   Round: {result['round']}")
        print(f"   Score: {result['score']:.4f}")
        print("---")

        print(f"{i+1}. Q: {result['question']}")
        print(f"   A: {result['answer']}")
        print(f"   Company: {result['company']}")
        print(f"   Role: {result['role']}")
        print(f"   Round: {result['round']}")
        print(f"   Score: {result['score']:.4f}")
        print("---")

        print(f"{i+1}. Q: {result['question']}")
        print(f"   A: {result['answer']}")
        print(f"   Company: {result['company']}")
        print(f"   Role: {result['role']}")
        print(f"   Round: {result['round']}")
        print(f"   Score: {result['score']:.4f}")
        print("---")
