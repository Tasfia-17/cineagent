# CineAgent 🎬

**One sentence → Cinematic short film with native audio**

Multi-agent AI pipeline powered by ByteDance Seedance 2.0.

---

## What It Does

Type one sentence. CineAgent's multi-agent system produces a complete cinematic short film with synchronized audio — no manual prompting, no editing, no post-processing.

**Demo**: *"A lone astronaut discovers an ancient alien artifact on Mars that begins to speak in a forgotten human language."* → 3-scene cinematic film with native audio in ~5 minutes.

---

## Agent Pipeline

```
Your Idea (1 sentence)
    │
    ▼
┌─────────────────────┐
│  Screenplay Agent   │  GPT-4o → 3-scene script with dialogue
└─────────┬───────────┘
          │
    ▼
┌─────────────────────┐
│   Director Agent    │  Enhances prompts with camera moves, lighting, style
└─────────┬───────────┘
          │
    ▼ (parallel × 3)
┌─────────────────────┐
│  Seedance 2.0 API   │  ByteDance video generation — native audio+video
│  (ByteDance)        │  T2V / I2V, 720p, 5s per clip
└─────────┬───────────┘
          │
    ▼
┌─────────────────────┐
│   Quality Agent     │  Scores each clip (0-10), retries with improved prompt if < 7
└─────────┬───────────┘
          │
    ▼
┌─────────────────────┐
│   Narrator Agent    │  ionrouter.io TTS → voiceover per scene
└─────────┬───────────┘
          │
    ▼
┌─────────────────────┐
│     Assembler       │  MoviePy → final .mp4
└─────────────────────┘
          │
    ▼
  🎬 Final Film
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Video Generation | [Seedance 2.0](https://www.byteplus.com/en/product/seedance) (ByteDance) |
| LLM Orchestration | GPT-4o-mini via OpenAI API |
| Speech / TTS | ionrouter.io (multilingual, real-time) |
| Video Assembly | MoviePy |
| Web UI | Gradio |
| REST API | FastAPI |

---

## Quick Start

```bash
git clone https://github.com/Tasfia-17/cineagent
cd cineagent
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

**Run the UI:**
```bash
python app.py
```

**Run from CLI:**
```bash
python pipeline.py "A street musician in Tokyo plays a melody that makes everyone remember their most precious memory."
```

**Run the API:**
```bash
uvicorn api.server:app --reload
```

---

## Project Structure

```
cineagent/
├── agents/
│   ├── screenplay_agent.py   # Turns idea → 3-scene screenplay
│   ├── director_agent.py     # Enhances prompts cinematically
│   ├── quality_agent.py      # Scores clips, triggers retries
│   └── narrator_agent.py     # Generates voiceover (ionrouter.io TTS)
├── core/
│   ├── video_engine.py       # Seedance 2.0 API client
│   └── assembler.py          # MoviePy video assembly
├── api/
│   └── server.py             # FastAPI REST API
├── pipeline.py               # Main orchestration pipeline
├── app.py                    # Gradio web UI
└── requirements.txt
```

---

## What Makes It Agentic (Not a Wrapper)

- **Autonomous decision-making**: Quality Agent scores each clip and decides whether to regenerate with an improved prompt — no human needed
- **Parallel execution**: All 3 video clips generate simultaneously via ThreadPoolExecutor
- **Error recovery**: Failed clips are retried with improved prompts automatically
- **Multi-agent coordination**: 4 specialized agents with distinct roles collaborate to produce output no single model could generate alone
- **Visible reasoning**: Every intermediate artifact (screenplay, storyboard, quality scores) is logged and inspectable

---

## Inspiration & References

This project was inspired by and builds upon ideas from:
- [ViMax](https://github.com/HKUDS/ViMax) — multi-agent video generation architecture
- [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) — automated video pipeline patterns
- [ShortGPT](https://github.com/RayVentura/ShortGPT) — content automation pipeline design
- [video-db/Director](https://github.com/video-db/Director) — video agent framework concepts

All code in this repository is original, written for the Seed Agents Challenge hackathon.

---

## Built For

[Beta University Seed Agents Challenge](https://betahacks.org) — April 2026  
Track: Most Creative (Multimodal Focus)

*Powered by ByteDance Seedance 2.0 · ionrouter.io · OpenAI*
