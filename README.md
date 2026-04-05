# DocxEditor API

A FastAPI service that accepts a `.docx` resume and a list of skills, inserts them as bullet points under the **Skills** section, and returns the edited file.

---

## Project Structure

```
docx-editor-api/
├── main.py
├── services/
│   └── docx_service.py
├── requirements.txt
├── render.yaml
└── README.md
```

---

## Local Setup

**1. Clone & create a virtual environment**
```bash
git clone <your-repo-url>
cd docx-editor-api
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run the server**
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

---

## API Reference

### `POST /add-skills`

| Field    | Type              | Description                                      |
|----------|-------------------|--------------------------------------------------|
| `file`   | `UploadFile`      | The `.docx` resume file                          |
| `skills` | `string` (Form)   | JSON array of skill strings                      |

**Success response:** edited `.docx` file as a binary download.  
**Error response:** `{ "detail": "..." }` with HTTP 400 / 404 / 500.

### `GET /health`

Returns `{ "status": "ok" }`.

---

## Usage Examples

### curl
```bash
curl -X POST http://localhost:8000/add-skills \
  -F "file=@resume.docx" \
  -F 'skills=["Docker", "Kubernetes", "FastAPI", "PostgreSQL"]' \
  --output edited_resume.docx
```

### Python
```python
import requests, json

with open("resume.docx", "rb") as f:
    response = requests.post(
        "http://localhost:8000/add-skills",
        files={"file": ("resume.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        data={"skills": json.dumps(["Docker", "Kubernetes", "FastAPI"])}
    )

with open("edited_resume.docx", "wb") as f:
    f.write(response.content)

print("Done! edited_resume.docx saved.")
```

---

## Skills Section Detection

The service searches for a paragraph whose text (case-insensitive) matches one of:

- `skills`
- `technical skills`
- `core skills`
- `key skills`

If none is found, the API returns **HTTP 404** with a descriptive error message.

---

## Deploy to Render.com

1. Push this repository to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service** → connect your repo.
3. Render will auto-detect `render.yaml` and configure the service.
4. Click **Deploy**. Your API will be live at `https://<service-name>.onrender.com`.

> The `render.yaml` already sets the build command, start command, and health check path — no manual configuration needed.
