# NetComply — AI-Augmented Network Compliance Engine (Prototype)

## Setup
```bash
pip install -r requirements.txt
python app.py
```
Then open http://127.0.0.1:5000

## Project layout
```
app.py                 Flask routes (dashboard, upload, training, reports)
models.py               CDM (Security Baseline Model) + Finding + Device
rule_engine.py           Vendor-agnostic CIS-style rules ("Deviation Analysis")
nlp_classifier.py        Keyword/pattern classifier + learned-mapping store
report_generator.py      ReportLab PDF report builder
parsers/
  base.py                Parser interface every vendor plugin implements
  cisco.py, juniper.py, paloalto.py
  detect.py               Vendor auto-detection + parser registry
sample_configs/          Cisco / Juniper / Palo Alto / "unknown vendor" samples
data/learned_mappings.json   Created automatically once you confirm a mapping
```

## Demo flow
1. `/upload` → load the **unknown_vendor.txt** sample and Analyze.
2. It parses partially; unrecognized lines route to `/training`.
3. Confirm the AI's suggested category for each line.
4. Re-scan the same file (or check the report) — the confirmed lines are now
   understood automatically, without touching any parser code.
5. `/report/<id>` → view findings + download the PDF.

## Extending to a new vendor
Add `parsers/<vendor>.py` implementing `matches()` and `parse()`, then register
it in `parsers/detect.py`. No changes needed to `rule_engine.py` or `app.py`.

## Notes for your writeup
- Deterministic rule engine handles PASS/FAIL — the classifier only *suggests*
  categories for unknown lines; a human always confirms before anything is
  learned. This keeps the compliance verdict auditable (see project chat for
  why a pure-LLM judgment call was rejected as the primary mechanism).
- In a production version, replace the in-memory `DEVICES`/`PENDING` dicts
  with a real database, and swap manual config paste for live device
  collection via Netmiko/NAPALM.
