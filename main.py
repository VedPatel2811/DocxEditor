import json
import logging

from fastapi import FastAPI, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse, Response

from services.docx_service import add_skills_to_resume, SkillsSectionNotFoundError

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="DocxEditor API")

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/add-skills")
async def add_skills(
    file: UploadFile,
    skills: str = Form(...),
):
    # Validate file type
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are accepted.")

    # Parse and validate skills
    try:
        skills_list: list = json.loads(skills)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="'skills' must be a valid JSON array.")

    if not isinstance(skills_list, list) or not skills_list:
        raise HTTPException(status_code=400, detail="'skills' must be a non-empty JSON array.")

    if not all(isinstance(s, str) for s in skills_list):
        raise HTTPException(status_code=400, detail="Every skill must be a string.")

    logger.info(f"Received file: {file.filename} | Skills: {skills_list}")

    file_bytes = await file.read()

    try:
        edited_bytes = add_skills_to_resume(file_bytes, skills_list)
    except SkillsSectionNotFoundError as e:
        logger.warning(str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process the document.")

    logger.info("Skills added successfully. Returning edited document.")
    return Response(
        content=edited_bytes,
        media_type=DOCX_MIME,
        headers={"Content-Disposition": 'attachment; filename="edited_resume.docx"'},
    )


# Catch-all for unhandled exceptions (safety net beyond HTTPException)
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"error": "Internal server error."})
