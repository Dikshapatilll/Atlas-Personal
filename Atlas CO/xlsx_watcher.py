import os
import time
import shutil
from pathlib import Path
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timezone
import re
import uuid




# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

WATCH_DIR = Path('Uploads')
ANALYZED_DIR = Path('ParsedExcel')

# Ensure ParsedExcel exists
ANALYZED_DIR.mkdir(parents=True, exist_ok=True)


def insert_report_and_parts_to_supabase(report, parts):
    # Insert report
    report_data = {
        "id": report["id"],
        "file_name": report["fileName"],
        "upload_date": report["uploadDate"],
        "total_parts_analyzed": report["totalPartsAnalyzed"],
        "sheet_stats": report["sheetStats"],
    }
    supabase.table("reports").insert(report_data).execute()
    # Insert parts
    if parts:
        supabase.table("part_numbers").insert(parts).execute()

def analyze_xlsx(file_path):
    try:
        df = pd.read_excel(file_path, sheet_name=None, header=None)
        report_id = f"report-{uuid.uuid4()}"
        upload_date = datetime.now(timezone.utc).isoformat()
        parsed_parts = []
        sheet_stats = []
        total_parts_analyzed = 0

        for sheet_name, sheet in df.items():
            json_data = sheet.values.tolist()
            total_rows = max(0, len(json_data) - 1)
            total_parts_analyzed += total_rows
            issue_rows = 0
            # Skip header row (index 0)
            for i, row in enumerate(json_data[1:], start=1):
                if not row or len(row) == 0:
                    continue
                part_value = str(row[0]).strip() if row[0] is not None else ''
                if not part_value:
                    continue
                surface_body_indicator = str(row[1]).lower() if len(row) > 1 and row[1] is not None else ''
                category = None
                # Prioritize checks
                if 'surface' in surface_body_indicator:
                    category = 'Surface Body'
                elif re.search(r'[^\u0000-\u007F]+', part_value):
                    category = 'Incorrect Naming'
                elif not re.search(r'\.SLD(PRT|ASM)$', part_value, re.IGNORECASE):
                    category = 'Missing Extension'
                elif not re.match(r'^\d{10}', part_value):
                    category = 'Non-10-Digit'
                if category:
                    issue_rows += 1
                    parsed_parts.append({
                        "id": f"part-{report_id}-{sheet_name}-{i}",
                        "value": part_value,
                        "category": category,
                        "report_id": report_id,
                        "date_added": upload_date,
                        "status": "open",
                        "date_corrected": None
                    })
            sheet_stats.append({
                "sheetName": sheet_name,
                "totalRows": total_rows,
                "issueRows": issue_rows
            })

        report = {
            "id": report_id,
            "fileName": file_path.name,
            "uploadDate": upload_date,
            "totalPartsAnalyzed": total_parts_analyzed,
            "sheetStats": sheet_stats,
        }
        # Insert into Supabase
        insert_report_and_parts_to_supabase(report, parsed_parts)
        print(f"Analyzed {file_path.name}: Sheets found: {[s for s in df.keys()]}")
    except Exception as e:
        print(f"Error analyzing {file_path.name}: {e}")

def main():
    print(f"Watching for new .xlsx files in {WATCH_DIR.resolve()}")
    while True:
        for file in WATCH_DIR.glob('*.xlsx'):
            try:
                analyze_xlsx(file)
                dest = ANALYZED_DIR / file.name
                # If a file with the same name exists, append a number to the filename
                base, ext = os.path.splitext(file.name)
                counter = 1
                while dest.exists():
                    dest = ANALYZED_DIR / f"{base}_copy{counter}{ext}"
                    counter += 1
                shutil.move(str(file), str(dest))
                print(f"Moved {file.name} to {dest}")
            except Exception as e:
                print(f"Error processing {file.name}: {e}")
        time.sleep(2)

if __name__ == "__main__":
    main()
