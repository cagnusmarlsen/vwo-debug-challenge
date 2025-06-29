## Bugs found
- The dependencies were a mess and could not be resolved easily at all. Fixed by removing unnecessary pinned dependencies; the correct versions of most conflicting dependencies was installed by crewai itself.
- The agent descriptions, backstories and tasks were inaccurate (although funny :P)
- fixed the BloodTestReportTool to extend the crewai BaseTool, added pdf loading functionality.

## Features added
- used rq (redis queue) to add concurrency
- added sqlite db connection to store analysis resutls 

# Project Setup and Execution Guide

## Getting Started

### Install Required Libraries

- **create virtual env**
```sh
python -m venv .venv
source .venv/bin/activate
```

```sh
pip install -r requirements.txt
```

- **create .env file and add:**
groq api key = https://console.groq.com/keys
```sh
GROQ_API_KEY=
SERPER_API_KEY=
REDIS_URL=
```  

- **iintialize db:**
```sh
alembic upgrade head
```

## Running the applcation

- start your redis server
  
- start the rq worker - 
```sh
rq worker default
```

-start the fastAPI app - 
```sh
python main.py
```

You can interact with the application through the FastAPI documentation, which is available at http://localhost:8000/docs. To analyze a blood test report, use the `/analyze` endpoint.

## API docs

  The API provides endpoints for analyzing blood test reports and retrieving the results.

  Health Check

   * Endpoint: GET /
   * Description: Checks if the API is running.
   * Response (200 OK):


        {
          "message": "Blood Test Report Analyser API is running"
        }


  Analyze Blood Report


   * Endpoint: POST /analyze
   * Description: Submits a blood test report (PDF) for analysis. This starts a background job.
   * Request Body: multipart/form-data
       * file (file, required): The PDF file of the blood test report.
       * query (string, optional): A specific question or instruction for the analysis. Defaults to "Summarise my Blood Test
         Report".
   * Response (200 OK):

        {
          "job_id": "a-unique-job-id",
          "analysis_id": 1,
          "status": "queued",
          "message": "Analysis started. Use the job_id to check status."
        }

   * Error Responses:
       * 400 Bad Request: If the uploaded file is not a PDF or is empty.
       * 500 Internal Server Error: If there is an error processing the file.

  Get Analysis Results


   * Endpoint: GET /results/{job_id}
   * Description: Retrieves the results of an analysis using the job_id.
   * Path Parameter:
       * job_id (string, required): The ID of the job returned by the /analyze endpoint.
   * Response (200 OK):
       * If the analysis is successful:


            {
              "status": "success",
              "job_status": "finished",
              "analysis_id": 1,
              "query": "Summarise my Blood Test Report",
              "result": "The complete analysis and recommendations from the AI agents.",
              "created_at": "2025-06-29T12:00:00.000Z"
            }

       * If the analysis has failed:


   1         {
   2           "status": "failed",
   3           "job_status": "failed",
   4           "error": "Details about the error that occurred.",
   5           "analysis_id": 1
   6         }

       * If the analysis is still in progress:


   1         {
   2           "status": "processing",
   3           "job_status": "started",
   4           "analysis_id": 1,
   5           "message": "Analysis is still processing. Please check back later."
   6         }

   * Error Responses:
       * 404 Not Found: If a job with the specified job_id is not found.

  Get Analysis Status


   * Endpoint: GET /status/{analysis_id}
   * Description: Retrieves the status of an analysis using the analysis_id.
   * Path Parameter:
       * analysis_id (integer, required): The database ID of the analysis.
   * Response (200 OK):


        {
          "analysis_id": 1,
          "status": "success",
          "job_id": "a-unique-job-id",
          "query": "Summarise my Blood Test Report",
          "created_at": "2025-06-29T12:00:00.000Z"
        }

   * Error Responses:
       * 404 Not Found: If an analysis with the specified analysis_id is not found.
