# -*- coding: utf-8 -*-

import threading
from sqlalchemy.orm import Session

from app.database.setup import get_db
from app.persistence.contract_repository import update_contract_processing_status
from app.utils.text_extractor import ContractProcessor


class BackgroundProcessor:
<<<<<<< HEAD
    """Service for processing contracts in background threads."""

=======

    
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    @staticmethod
    def process_contract_async(
        contract_id: int,
        user_id: int,
        file_path: str,
        file_type: str
    ):
<<<<<<< HEAD
        """Process contract file asynchronously in background thread."""
        def process_in_background():
            try:
                # Get database session
                db = next(get_db())
                
                # Update contract status to processing
=======

        def process_in_background():
            try:
   
                db = next(get_db())
                
 
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                update_contract_processing_status(
                    db=db,
                    contract_id=contract_id,
                    user_id=user_id,
                    status="processing"
                )
                
<<<<<<< HEAD
                # Extract sentences from contract file
=======
   
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                ContractProcessor.process_contract(
                    db=db,
                    contract_id=contract_id,
                    user_id=user_id,
                    file_path=file_path,
                    file_type=file_type
                )
                
                print(f"Background processing completed for contract {contract_id}")

<<<<<<< HEAD
                # Create analysis job record
=======
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                from uuid import uuid4
                from datetime import datetime, timezone
                from pathlib import Path
                import os
                import pandas as pd
                from app.database.models.analysis_job import AnalysisJob
                from app.database.models.contract_sentence import ContractSentence
                from app.persistence.contract_repository import get_contract_by_id

                job_id = str(uuid4())
                contract = get_contract_by_id(db, contract_id, user_id)
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None

                started_at = datetime.now(timezone.utc)
                job = AnalysisJob(
                    id=job_id,
                    user_id=user_id,
                    contract_id=contract_id,
                    file_name=contract.file_name,
                    file_type=contract.file_type,
                    file_size=file_size,
                    status="PROCESSING",
                    uploaded_at=started_at,
                    started_at=started_at
                )
                db.add(job)
                db.commit()

<<<<<<< HEAD
                # Load extracted sentences from CSV and save to database
=======
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                import os
                # Use persistent disk if OUTPUT_DIR is set (for Render), otherwise use backend/outputs
                if os.getenv("OUTPUT_DIR"):
                    output_base = Path(os.getenv("OUTPUT_DIR"))
                else:
                    backend_dir = Path(__file__).resolve().parents[3]
                    output_base = backend_dir / "outputs"
                output_root = output_base / str(user_id) / str(contract_id)
                csv_path = output_root / "sentences.csv"
                if not csv_path.exists():
<<<<<<< HEAD
                    # Fallback to first subdir CSV
=======
                    # fallback to first subdir CSV
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                    csv_path = None
                    for p in output_root.iterdir():
                        if p.is_dir():
                            candidate = p / "sentences.csv"
                            if candidate.exists():
                                csv_path = candidate
                                break
                if csv_path and csv_path.exists():
                    df = pd.read_csv(csv_path, encoding="utf-8")
                    objs = []
                    for _, row in df.iterrows():
                        objs.append(ContractSentence(
                            job_id=job_id,
                            contract_id=contract_id,
                            file_name=str(row.get("file_name") or contract.file_name or ""),
                            file_type=str(row.get("file_type") or contract.file_type or ""),
                            page=int(row.get("page")) if not pd.isna(row.get("page")) else None,
                            sentence_id=int(row.get("sentence_id")) if not pd.isna(row.get("sentence_id")) else None,
                            section=None,
                            subsection=None,
                            sentence=str(row.get("sentence") or ""),
                            sentence_vec=None,
                            label=None,
                            is_ambiguous=None,
                            explanation=None,
                            suggested_revision=None,
                            clarity_score=None
                        ))
                    if objs:
                        db.bulk_save_objects(objs)
                        db.commit()
                        total_sentences = len(objs)
                    else:
                        total_sentences = 0
                else:
                    total_sentences = 0

<<<<<<< HEAD
                # Update job status to completed
=======
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                finished_at = datetime.now(timezone.utc)
                job.status = "COMPLETED"
                job.finished_at = finished_at
                job.progress_pct = 100.0
                job.total_sentences = total_sentences
                job.duration_seconds = (finished_at - started_at).total_seconds()
                db.commit()

            except Exception as e:
<<<<<<< HEAD
                # Handle errors: update contract and job status to failed
=======
   
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                try:
                    db = next(get_db())
                    update_contract_processing_status(
                        db=db,
                        contract_id=contract_id,
                        user_id=user_id,
                        status="failed"
                    )

                    try:
                        from sqlalchemy import select
                        from app.database.models.analysis_job import AnalysisJob
                        job = db.scalar(select(AnalysisJob).where(AnalysisJob.contract_id == contract_id, AnalysisJob.user_id == user_id).limit(1))
                        if job:
                            from datetime import datetime, timezone
                            job.status = "FAILED"
                            job.finished_at = datetime.now(timezone.utc)
                            db.commit()
                    except:
                        pass
                except:
                    pass
                
                print(f"Background processing failed for contract {contract_id}: {e}")
        
<<<<<<< HEAD
        # Start background thread
=======
  
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()