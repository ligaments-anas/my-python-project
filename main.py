from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from utils import analyze_text, analyze_uploaded_file, generate_pdf
import os
import uuid

# Initialize FastAPI
app = FastAPI()

# Enable CORS for frontend usage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL for security
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure report directory exists
REPORT_DIR = "./reports"
os.makedirs(REPORT_DIR, exist_ok=True)


# WebSocket endpoint for real-time problem statements
@app.websocket("/ws/analyze")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "status", "message": "Analyzing input..."})
            result = await analyze_text(data)

            filename = f"report_{uuid.uuid4()}.pdf"
            generate_pdf(result["original_input"], result["summary"], filename)

            await websocket.send_json({
                "type": "result",
                "summary": result["summary"],
                "download_url": f"/reports/{filename}"
            })

    except WebSocketDisconnect:
        print("WebSocket disconnected.")


# REST API for file upload analysis (.txt, .pdf, .docx)
@app.post("/analyze-file")
async def analyze_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".txt", ".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only .txt, .pdf, .docx files supported.")

    result = await analyze_uploaded_file(file)
    filename = f"report_{uuid.uuid4()}.pdf"
    generate_pdf(result["original_input"], result["summary"], filename)

    return {
        "summary": result["summary"],
        "download_url": f"/reports/{filename}"
    }


# Serve generated PDF reports
@app.get("/reports/{filename}")
def get_report(filename: str):
    file_path = os.path.join(REPORT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path=file_path, media_type='application/pdf', filename=filename)
