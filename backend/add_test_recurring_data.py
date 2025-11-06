#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Add test data for recurring ambiguous sentences
Usage:
    python add_test_recurring_data.py [user_id] [--database-path /path/to/db]
    
    If --database-path is not specified, will use DATABASE_PATH environment variable
    or default to app.db in the backend directory.
"""
import sys
import os
import argparse
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set DATABASE_PATH if provided as argument
if '--database-path' in sys.argv:
    idx = sys.argv.index('--database-path')
    if idx + 1 < len(sys.argv):
        os.environ['DATABASE_PATH'] = sys.argv[idx + 1]
        # Remove from sys.argv so argparse doesn't see it
        sys.argv.pop(idx)
        sys.argv.pop(idx)

from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database.setup import get_db
from app.database.models.contract import Contract
from app.database.models.contract_sentence import ContractSentence
from app.database.models.analysis_job import AnalysisJob
from app.database.models.user import User
from datetime import datetime, timezone
from uuid import uuid4

def add_test_recurring_data(user_id: int = 1):
    """Add test data for recurring ambiguous sentences"""
    db: Session = next(get_db())
    
    try:
        # 1. Check if user exists
        user = db.scalar(select(User).where(User.id == user_id))
        if not user:
            print(f"User ID {user_id} not found!")
            return
        
        print(f"Found user: {user.email} (ID: {user_id})")
        
        # 2. Find or create a contract for this user
        contract = db.scalar(select(Contract).where(
            Contract.user_id == user_id,
            Contract.is_active == True
        ).limit(1))
        
        if not contract:
            print(f"No contract found for user {user_id}, creating one...")
            contract = Contract(
                title="Test Contract for Recurring Sentences",
                description="Test contract",
                user_id=user_id,
                processing_status="completed",
                file_name="test_recurring.pdf",
                file_type=".pdf",
                is_active=True
            )
            db.add(contract)
            db.commit()
            db.refresh(contract)
            print(f"Created contract ID: {contract.id}")
        else:
            print(f"Using existing contract ID: {contract.id}")
        
        # 3. Find or create an analysis_job
        job = db.scalar(select(AnalysisJob).where(
            AnalysisJob.contract_id == contract.id,
            AnalysisJob.user_id == user_id
        ).limit(1))
        
        if not job:
            print(f"Creating analysis job...")
            job = AnalysisJob(
                id=str(uuid4()),
                user_id=user_id,
                contract_id=contract.id,
                file_name=contract.file_name or "test_recurring.pdf",
                file_type=contract.file_type or ".pdf",
                status="COMPLETED",
                uploaded_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc),
                finished_at=datetime.now(timezone.utc)
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            print(f"Created job ID: {job.id}")
        else:
            print(f"Using existing job ID: {job.id}")
        
        # 4. Define recurring ambiguous sentences (these will appear multiple times)
        recurring_sentences = [
            "The terms of this agreement may be interpreted in different ways.",
            "Any party may terminate this contract at their discretion.",
            "All disputes shall be resolved through appropriate legal channels.",
            "The company reserves the right to modify these terms without notice.",
            "Payment shall be made in accordance with the standard procedures."
        ]
        
        # 5. Insert sentences - each sentence appears 3-5 times across different pages
        existing_count = db.scalar(select(func.count(ContractSentence.id)).where(
            ContractSentence.contract_id == contract.id
        )) or 0
        
        sentence_id_start = existing_count + 1
        
        print(f"\nInserting recurring ambiguous sentences...")
        inserted = 0
        
        for idx, sentence in enumerate(recurring_sentences):
            # Each sentence appears 3-5 times
            frequency = 3 + (idx % 3)  # 3, 4, or 5 times
            
            for repeat in range(frequency):
                page = 1 + (repeat % 3)  # Pages 1, 2, or 3
                sentence_id = sentence_id_start + (idx * 10) + repeat
                
                contract_sentence = ContractSentence(
                    job_id=job.id,
                    contract_id=contract.id,
                    file_name=contract.file_name or "test_recurring.pdf",
                    file_type=contract.file_type or ".pdf",
                    page=page,
                    sentence_id=sentence_id,
                    sentence=sentence,
                    is_ambiguous=True,  # Mark as ambiguous
                    label="AMBIGUOUS",
                    explanation="This sentence contains ambiguous language that may be interpreted in multiple ways.",
                    clarity_score=0.5  # Low clarity score
                )
                db.add(contract_sentence)
                inserted += 1
        
        db.commit()
        print(f"Inserted {inserted} sentences ({len(recurring_sentences)} unique sentences, {sum(3 + (i % 3) for i in range(len(recurring_sentences)))} total)")
        
        # 6. Verify the data
        print(f"\nVerifying data...")
        result = db.execute(
            select(ContractSentence.sentence, func.count(ContractSentence.id).label('count'))
            .where(
                ContractSentence.contract_id == contract.id,
                ContractSentence.is_ambiguous == True
            )
            .group_by(ContractSentence.sentence)
            .having(func.count(ContractSentence.id) > 1)
            .order_by(func.count(ContractSentence.id).desc())
        ).all()
        
        print(f"Found {len(result)} recurring ambiguous sentences:")
        for row in result[:10]:  # Show first 10
            print(f"  - '{row.sentence[:60]}...' appears {row.count} times")
        
        print(f"\n[SUCCESS] Test data added successfully!")
        print(f"   Contract ID: {contract.id}")
        print(f"   Job ID: {job.id}")
        print(f"   Total sentences: {inserted}")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add test data for recurring ambiguous sentences')
    parser.add_argument('user_id', type=int, nargs='?', default=1, help='User ID (default: 1)')
    parser.add_argument('--database-path', type=str, help='Path to database file (overrides DATABASE_PATH env var)')
    
    args = parser.parse_args()
    
    # Set DATABASE_PATH if provided
    if args.database_path:
        os.environ['DATABASE_PATH'] = args.database_path
    
    # Show database path being used
    db_path = os.environ.get('DATABASE_PATH', 'app.db (default)')
    print(f"Using database: {db_path}")
    print(f"Adding test data for user ID: {args.user_id}\n")
    
    add_test_recurring_data(args.user_id)

