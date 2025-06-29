from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
import os
import uuid
from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

import models
from database import engine, get_db
from worker import run_crew

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Blood Test Report Analyser")

# Redis connection - specify queue name explicitly
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
q = Queue('default', connection=redis_conn)  # Explicitly name the queue

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Blood Test Report Analyser API is running"}

@app.post("/analyze")
async def analyze_blood_report(
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    query: str = Form(default="Summarise my Blood Test Report")
):
    """Analyze blood test report and provide comprehensive health recommendations"""
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Generate unique filename to avoid conflicts
    file_id = str(uuid.uuid4())
    file_path = f"data/blood_test_report_{file_id}.pdf"
    
    new_analysis = None
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Empty file uploaded")
            f.write(content)
        
        # Validate query
        if not query or query.strip() == "":
            query = "Summarise my Blood Test Report"

        # Create a new user and analysis record
        new_user = models.User()
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        new_analysis = models.Analysis(
            query=query.strip(),
            file_path=file_path,
            user_id=new_user.id,
            status="queued"  # Set initial status
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)

        # Pass analysis_id to the job
        job = q.enqueue(
            'worker.run_crew',
            new_analysis.id,
            job_timeout=1800,  # 30 minutes timeout
        )

        new_analysis.job_id = job.get_id()
        db.commit()

        return {
            "job_id": job.get_id(),
            "analysis_id": new_analysis.id,
            "status": "queued",
            "message": "Analysis started. Use the job_id to check status."
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        # Clean up file if it was created
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
        raise
        
    except Exception as e:
        # Clean up database record and file on error
        if new_analysis:
            try:
                db.delete(new_analysis)
                db.commit()
            except:
                db.rollback()
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
                
        raise HTTPException(status_code=500, detail=f"Error processing blood report: {str(e)}")

@app.get("/results/{job_id}")
async def get_results(job_id: str, db: Session = Depends(get_db)):
    """Get the results of a job"""
    try:
        analysis = db.query(models.Analysis).filter(models.Analysis.job_id == job_id).first()

        if not analysis:
            raise HTTPException(status_code=404, detail="Job not found")

        # Get job status from Redis
        from rq.job import Job
        try:
            job = Job.fetch(job_id, connection=redis_conn)
            job_status = job.get_status()
        except:
            job_status = "unknown"

        if analysis.status == "success":
            return {
                "status": "success",
                "job_status": job_status,
                "analysis_id": analysis.id,
                "query": analysis.query,
                "result": analysis.result,
                "created_at": analysis.created_at
            }
        elif analysis.status == "failed":
            error_message = getattr(analysis, 'error_message', 'Job failed to process')
            return {
                "status": "failed", 
                "job_status": job_status,
                "error": error_message,
                "analysis_id": analysis.id
            }
        else:
            return {
                "status": analysis.status or "processing",
                "job_status": job_status,
                "analysis_id": analysis.id,
                "message": "Analysis is still processing. Please check back later."
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving results: {str(e)}")

@app.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: int, db: Session = Depends(get_db)):
    """Get analysis status by analysis ID"""
    analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    return {
        "analysis_id": analysis.id,
        "status": analysis.status,
        "job_id": analysis.job_id,
        "query": analysis.query,
        "created_at": analysis.created_at
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


