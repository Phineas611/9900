"""
Script to add test sentences directly to the database.
This can be run locally or on Render to add test data.
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.database.setup import get_db, create_tables
from app.database.models.contract_sentence import ContractSentence
from app.database.models.contract import Contract
from app.database.models.analysis_job import AnalysisJob
from app.database.models.user import User
from datetime import datetime, timezone
import uuid

# Test sentences - some will be repeated to test recurring phrases
TEST_SENTENCES = [
    "The Company may terminate this agreement at any time without notice.",
    "The Company may terminate this agreement at any time without notice.",
    "The Company may terminate this agreement at any time without notice.",
    "Either party may terminate this agreement upon thirty days written notice.",
    "Either party may terminate this agreement upon thirty days written notice.",
    "Either party may terminate this agreement upon thirty days written notice.",
    "The parties agree that any dispute shall be resolved through arbitration.",
    "The parties agree that any dispute shall be resolved through arbitration.",
    "This agreement shall be governed by the laws of the State of New York.",
    "This agreement shall be governed by the laws of the State of New York.",
    "The parties hereby agree to keep all confidential information strictly confidential.",
]

def get_or_create_user(db: Session, email: str = "test@example.com") -> User:
    """Get or create a test user"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            name="Test User",
            password_hash="test_hash"  # For testing only
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created user: {user.id} ({user.email})")
    else:
        print(f"Using existing user: {user.id} ({user.email})")
    return user

def get_or_create_contract(db: Session, user_id: int, title: str = "Test Contract") -> Contract:
    """Get or create a test contract"""
    contract = db.query(Contract).filter(
        Contract.user_id == user_id,
        Contract.title == title
    ).first()
    
    if not contract:
        contract = Contract(
            title=title,
            description="Test contract for recurring phrases endpoint",
            user_id=user_id,
            file_name="test_contract.pdf",
            file_type=".pdf",
            processing_status="completed"
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
        print(f"Created contract: {contract.id} ({contract.title})")
    else:
        print(f"Using existing contract: {contract.id} ({contract.title})")
    return contract

def get_or_create_job(db: Session, contract_id: int, user_id: int) -> AnalysisJob:
    """Get or create a test analysis job"""
    job = db.query(AnalysisJob).filter(
        AnalysisJob.contract_id == contract_id
    ).first()
    
    if not job:
        job = AnalysisJob(
            id=str(uuid.uuid4()),
            user_id=user_id,
            contract_id=contract_id,
            status="completed"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        print(f"Created job: {job.id}")
    else:
        print(f"Using existing job: {job.id}")
    return job

def add_test_sentences(
    db: Session,
    contract_id: int,
    job_id: str,
    sentences: list,
    mark_ambiguous: bool = False
):
    """
    Add test sentences to the database.
    
    Args:
        db: Database session
        contract_id: Contract ID
        job_id: Job ID
        sentences: List of sentences to add
        mark_ambiguous: If True, mark all sentences as ambiguous
    """
    print(f"\nAdding {len(sentences)} sentences to contract {contract_id}...")
    
    added_count = 0
    skipped_count = 0
    
    for idx, sentence_text in enumerate(sentences):
        # Check if sentence already exists (exact match)
        existing = db.query(ContractSentence).filter(
            ContractSentence.contract_id == contract_id,
            ContractSentence.sentence == sentence_text
        ).first()
        
        if existing:
            # Update existing sentence
            if mark_ambiguous:
                existing.is_ambiguous = True
                existing.label = "AMBIGUOUS"
            added_count += 1
            continue
        
        # Create new sentence record
        sentence = ContractSentence(
            job_id=job_id,
            contract_id=contract_id,
            file_name="test_contract.pdf",
            file_type=".pdf",
            page=(idx % 10) + 1,  # Distribute across pages 1-10
            sentence_id=idx + 1,
            sentence=sentence_text,
            is_ambiguous=mark_ambiguous,
            label="AMBIGUOUS" if mark_ambiguous else None,
            explanation=f"Test sentence {idx + 1}" if mark_ambiguous else None,
            clarity_score=0.6 if mark_ambiguous else None
        )
        db.add(sentence)
        added_count += 1
    
    db.commit()
    print(f"Successfully added/updated {added_count} sentences")
    
    # Count how many times each sentence appears
    from collections import Counter
    sentence_counts = Counter(sentences)
    recurring = {s: count for s, count in sentence_counts.items() if count > 1}
    
    if recurring:
        print(f"\nRecurring sentences (will appear in /api/phrases/recurring):")
        for sentence, count in sorted(recurring.items(), key=lambda x: x[1], reverse=True):
            print(f"  - '{sentence[:60]}...' appears {count} times")

def main():
    """Main function"""
    print("=" * 70)
    print("Adding test sentences to database")
    print("=" * 70)
    
    # Create tables if they don't exist
    create_tables()
    
    # Get database session
    db = next(get_db())
    
    try:
        # Get or create user, contract, and job
        user = get_or_create_user(db)
        contract = get_or_create_contract(db, user.id, "Test Contract for Recurring Phrases")
        job = get_or_create_job(db, contract.id, user.id)
        
        # Add test sentences and mark them as ambiguous
        add_test_sentences(
            db=db,
            contract_id=contract.id,
            job_id=job.id,
            sentences=TEST_SENTENCES,
            mark_ambiguous=True  # Mark all as ambiguous for recurring phrases test
        )
        
        print("\n" + "=" * 70)
        print("Test data added successfully!")
        print("=" * 70)
        print(f"\nContract ID: {contract.id}")
        print(f"Job ID: {job.id}")
        print("\nYou can now test the recurring phrases endpoint:")
        print("GET /api/phrases/recurring?limit=20")
        print("\nExpected result: Should return recurring ambiguous phrases")
        
    except Exception as e:
        print(f"\nERROR: Failed to add test data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()

