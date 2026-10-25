# Sahulat

Qwen-powered assistant (Alibaba Cloud Model Studio) that explains bills, notices and
official letters in simple Urdu or English, with tool calls for fees and helplines.

## Run
    pip install -r requirements.txt
    export DASHSCOPE_API_KEY=...   # from Alibaba Cloud Model Studio; omit for offline mock mode
    python app.py                  # http://localhost:8000
    python -m pytest tests

## Next steps to make it competition-ready
- Pick one narrow user (e.g. farmers, flood victims, small shopkeepers) and tailor prompts/tools.
- Add document upload (Qwen-VL) and an Urdu voice interface.
- Deploy on Alibaba Cloud and record a 2-minute demo with real impact numbers.
