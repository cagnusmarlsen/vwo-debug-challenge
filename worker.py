import os
from redis import Redis
import traceback
from rq import Worker, Queue
from sqlalchemy.orm import Session
import logging
import models
from database import SessionLocal
from crewai import Crew, Process
from agents import doctor, verifier, nutritionist, exercise_specialist
from task import help_patients, nutrition_analysis, exercise_planning, verification
from tools import blood_test_tool

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
conn = Redis.from_url(redis_url)

def run_crew(analysis_id: int):
    """To run the whole crew and update the database"""
    
    db: Session = SessionLocal()
    analysis = None
    
    try:
        analysis = db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()
        if not analysis:
            return {"error": f"Analysis with id {analysis_id} not found"}

        analysis.status = "processing"
        db.commit()

        # Check if file exists before starting crew
        if not os.path.exists(analysis.file_path):
            error_msg = f"File not found: {analysis.file_path}"
            analysis.status = "failed"
            analysis.error_message = error_msg
            db.commit()
            return {"error": error_msg}
        
        medical_crew = Crew(
            agents=[verifier, doctor, nutritionist, exercise_specialist],
            tasks=[verification, help_patients, nutrition_analysis, exercise_planning],
            process=Process.sequential,
            verbose=True
        )

        # Use more specific inputs
        inputs = {
            'query': analysis.query, 
            'file_path': analysis.file_path
        }
        
        result = medical_crew.kickoff(inputs)

        analysis.result = str(result)
        analysis.status = "success"
        db.commit()
        
        return {"success": True, "result": str(result)}

    except Exception as e:
        # Get full traceback
        error_traceback = traceback.format_exc()
        
        if analysis:
            analysis.status = "failed"
            analysis.error_message = f"{str(e)}\n\nTraceback:\n{error_traceback}"
            try:
                db.commit()
            except Exception as commit_error:
                print(f"Error updating failed status: {commit_error}")
                db.rollback()
        
        return {"error": str(e), "traceback": error_traceback}

    finally:
        # Clean up file
        if analysis and analysis.file_path and os.path.exists(analysis.file_path):
            try:
                os.remove(analysis.file_path)
            except OSError as e:
                print(f"Error cleaning up file {analysis.file_path}: {e}")
        
        db.close()

if __name__ == '__main__':
    # Create queue and worker
    worker = Worker(['default'], connection=conn)
    
    print("Starting RQ worker...")
    worker.work()