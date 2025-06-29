## Importing libraries and files
from crewai import Task

from agents import doctor, verifier, nutritionist, exercise_specialist
from tools import search_tool, blood_test_tool


## Creating a task to verify the blood test report
verification = Task(
    description="Verify that the uploaded document with {file_path} is a valid blood test report. "
                "Use the blood_test_tool to extract the full content of the report."
                "Check for standard medical markers and report any missing or unusual information. "
                "Confirm that the file is a readable PDF document.",

    expected_output="""A verification report, stating:
- Whether the document is a valid blood test report.
- Any inconsistencies or missing information found.
- The full content of the blood test report.""",

    agent=verifier,
    tools=[blood_test_tool],
    async_execution=False,
)

## Creating a task to help solve user's query
help_patients = Task(
    description="Analyze the user's query: {query} and the provided blood test report. "
                "Provide a clear and concise summary of the blood test results, highlighting any abnormalities. "
                "Offer general health recommendations based on the findings. "
                "Use the search tool to find relevant medical information and cite your sources.",

    expected_output="""A comprehensive analysis of the blood test report, including:
- A summary of the key findings.
- An explanation of any abnormalities detected.
- General health recommendations based on the results.
- Links to credible sources for further reading.""",

    agent=doctor,
    tools=[search_tool],
    async_execution=False,
    context=[verification]
)

## Creating a nutrition analysis task
nutrition_analysis = Task(
    description="Analyze the blood test report to assess the user's nutritional status. "
                "Based on the user's query: {query} and the blood test results, provide personalized dietary recommendations. "
                "Focus on evidence-based nutrition and sustainable lifestyle changes.",

    expected_output="""A personalized nutrition plan, including:
- An assessment of the user's current nutritional status.
- Specific dietary recommendations to address any deficiencies or imbalances.
- A sample meal plan.
- Advice on healthy eating habits.
- Recommendations for supplements only if necessary and supported by evidence.""",

    agent=nutritionist,
    tools=[search_tool],
    async_execution=False,
    context=[verification]
)

## Creating an exercise planning task
exercise_planning = Task(
    description="Develop a safe and effective exercise plan based on the user's blood test report and query: {query}. "
                "Consider the user's fitness level, health conditions, and goals. "
                "Provide a balanced workout routine that includes cardiovascular, strength, and flexibility exercises.",

    expected_output="""A customized exercise plan, including:
- A recommended workout schedule.
- Detailed instructions for each exercise, including modifications for different fitness levels.
- Guidelines for warm-up and cool-down.
- Advice on how to progress safely and effectively.""",

    agent=exercise_specialist,
    tools=[search_tool],
    async_execution=False,
    context=[verification]
)
