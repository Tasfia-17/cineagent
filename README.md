# ShopReel 🛍️🎬

**Add a product → 5 platform-optimized videos in minutes. Automatically.**

Always-on ecommerce video agent powered by ByteDance Seedance 2.0 + Seedream 5.0.

---

## What It Does

Connect your Shopify store. Every time you add a product, ShopReel's agent pipeline automatically generates 5 platform-ready videos — no human input needed.

| Platform | Format | Duration |
|---|---|---|
| TikTok | 9:16 vertical | 15s |
| Instagram Reels | 9:16 vertical | 15s |
| YouTube Short | 16:9 landscape | 30s |
| Amazon Listing | 16:9 landscape | 30s |
| Product Page | 1:1 square | 10s |

**Demo**: Add a product to a Shopify store → watch 5 videos appear in real-time.

---

## Agent Pipeline

```
Shopify webhook: products/create
        │
        ▼
┌─────────────────────┐
│   Script Agent      │  Pollinations LLM → 5 platform-specific scripts + hooks
└─────────┬───────────┘
          │
    ▼ (×5 platforms, parallel)
┌─────────────────────┐
│  Seedream 5.0       │  Product keyframe image per platform
│  (ByteDance)        │
└─────────┬───────────┘
          │
┌─────────────────────┐
│  Seedance 2.0 I2V   │  keyframe + script → video clip (native audio)
│  (ByteDance)        │
└─────────┬───────────┘
          │
┌─────────────────────┐
│  Quality Agent      │  Scores hook strength + CTA clarity, auto-retries
└─────────┬───────────┘
          │
┌─────────────────────┐
│  Narrator Agent     │  edge-tts voiceover per platform
└─────────────────────┘
          │
    ▼
  5 platform videos ready
```

---

## Quick Start

```bash
git clone https://github.com/Tasfia-17/cineagent
cd cineagent
pip install -r requirements.txt
cp .env.example .env
```

**Run the UI (manual demo):**
```bash
python app.py
```

**Run the API + Shopify webhook:**
```bash
uvicorn api.server:app --reload --port 8000
# In another terminal:
ngrok http 8000
# Register https://YOUR_NGROK_URL/webhook/shopify in Shopify admin
```

---

## Shopify Webhook Setup (5 minutes)

1. Create free dev store at [shopify.com/partners](https://shopify.com/partners)
2. Run `ngrok http 8000` → copy the HTTPS URL
3. Shopify Admin → Settings → Notifications → Webhooks → Add webhook
   - Event: `Product creation`
   - URL: `https://YOUR_NGROK_URL/webhook/shopify`
4. Copy the webhook signing secret → paste in `.env` as `SHOPIFY_WEBHOOK_SECRET`
5. Add a product → watch 5 videos generate automatically

---

## Project Structure

```
cineagent/
├── agents/
│   ├── script_agent.py       # 5 platform-specific ad scripts
│   ├── quality_agent.py      # hook strength + CTA scoring
│   └── narrator_agent.py     # edge-tts voiceover
├── core/
│   ├── video_engine.py       # Seedance 2.0 async client
│   ├── keyframe_engine.py    # Seedream 5.0 keyframe generation
│   └── llm_providers.py      # Pollinations (free) + fallbacks
├── api/
│   └── server.py             # FastAPI + Shopify webhook handler
├── shopreel_pipeline.py      # Main orchestration (5 parallel videos)
├── pipeline.py               # Original CineAgent pipeline
└── app.py                    # Gradio UI
```

---

## Inspiration & References

- [ViMax](https://github.com/HKUDS/ViMax) — multi-agent video pipeline architecture
- [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) — automated video pipeline patterns
- [ShortGPT](https://github.com/RayVentura/ShortGPT) — content automation design

All code is original, written for the Seed Agents Challenge hackathon.

---

## Built For

[Beta University Seed Agents Challenge](https://betahacks.org) — April 2026
**Track 2: AI-Powered Content Automation**

*Powered by ByteDance Seedance 2.0 · Seedream 5.0 · Pollinations.ai*
