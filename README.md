# Math Mentor Application

A Reliable Multimodal Math Mentor using LangGraph (Agentic Workflow), Streamlit (UI), and RAG.

## Features
- **Multimodal Inputs**: Accepts Text, Image (OCR via Tesseract), and Audio (Whisper via Groq).
- **RAG + Memory Layer**: Leverages local ChromaDB with math documents and an SQLite persistent memory to retrieve past solved problems.
- **Human-in-the-Loop (HITL)**: Users can review OCR/audio transcripts before solving, interact when the Parser Agent gets confused, and provide correct/incorrect feedback which is saved to Memory.
- **Multi-Agent Architecture**: Uses `langgraph` with 5 distinct agents:
  1. Parser Agent
  2. Intent Router
  3. Solver Agent
  4. Verifier / Critic Agent
  5. Explainer / Tutor Agent

## Local Setup

### 1. Prerequisites
- Python 3.9+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed on your system.

### 2. Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
Ensure you set:
- `GROQ_API_KEY`: Your Groq API Key.
- `TESSERACT_CMD`: Path to your tesseract executable (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe` on Windows or `/usr/local/bin/tesseract` on Mac).

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the App
```bash
streamlit run app.py
```
The application will launch on `http://localhost:8501`.

## Deployment
To deploy this on Streamlit Community Cloud:
1. Push this code to a public GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and connect your repository.
3. In the Streamlit Cloud dashboard, configure the **Secrets** to include your `GROQ_API_KEY`.
*(Note: Streamlit cloud environments use Linux. Tesseract can usually be installed via a `packages.txt` file containing `tesseract-ocr`)*.
