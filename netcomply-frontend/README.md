# NetComply — React Frontend

Talks to the Flask JSON API in `../netcomply/api.py`.

## Setup
```bash
cd netcomply-frontend
npm install
npm run dev
```

This starts both the Flask API (`http://127.0.0.1:5000`) and the Vite frontend
(`http://127.0.0.1:5173`). Install Python dependencies first with
`python -m pip install -r ../netcomply/requirements.txt`.

## Structure
```
src/
  api.js                 fetch wrapper — the only file that knows backend URLs
  App.jsx                routes: / , /upload , /training , /report/:deviceId
  components/
    Nav.jsx               top nav, shows pending-training badge
    Dashboard.jsx          aggregate stats + scanned device list
    Upload.jsx              paste/upload config, load vendor samples
    Training.jsx            confirm AI-suggested categories for unknown lines
    Report.jsx               per-device findings table + PDF download link
```

## Demo flow
1. Start both servers above.
2. Upload &amp; Scan → click the `unknown_vendor.txt` sample chip → Analyze.
3. Go to AI Training → confirm the suggested category for each flagged line.
4. Re-run the same sample (or check Dashboard) — those lines are now understood
   automatically, no code changes needed.
