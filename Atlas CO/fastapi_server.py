import os
import shutil
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import uvicorn
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

WATCH_DIR = Path('Uploads')
ANALYZED_DIR = Path('ParsedExcel')

app = FastAPI()

# Allow CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

websocket_clients = set()

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def insert_report_to_supabase(filename, sheets):
    data = {
        "filename": filename,
        "sheets": sheets,
        "analyzed_at": datetime.utcnow().isoformat()
    }
    supabase.table("analyzed_reports").insert(data).execute()

async def analyze_xlsx(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name=None)
        sheets = list(df.keys())
        insert_report_to_supabase(file_path.name, sheets)
        return {"filename": file_path.name, "sheets": sheets}
    except Exception as e:
        return {"filename": file_path.name, "error": str(e)}

async def watcher_task():
    ANALYZED_DIR.mkdir(parents=True, exist_ok=True)
    while True:
        for file in WATCH_DIR.glob('*.xlsx'):
            try:
                result = await analyze_xlsx(file)
                dest = ANALYZED_DIR / file.name
                # If a file with the same name exists, append a number to the filename
                base, ext = os.path.splitext(file.name)
                counter = 1
                while dest.exists():
                    dest = ANALYZED_DIR / f"{base}_copy{counter}{ext}"
                    counter += 1
                shutil.move(str(file), str(dest))
                # Notify all websocket clients
                for ws in list(websocket_clients):
                    try:
                        await ws.send_json({"type": "analyzed", **result})
                    except Exception:
                        websocket_clients.discard(ws)
            except Exception as e:
                print(f"Error processing {file.name}: {e}")
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(watcher_task())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        websocket_clients.discard(websocket)

if __name__ == "__main__":
    uvicorn.run("fastapi_server:app", host="0.0.0.0", port=8000, reload=True)
