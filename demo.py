"""
ShopReel Demo Simulator
Realistic demo that simulates a live Shopify store + autonomous agent pipeline.
For demo/presentation purposes — shows exactly what the real product does.
"""

import gradio as gr
import json
import time
import threading
import asyncio
from demo_pipeline import run_demo_pipeline

# Pre-loaded demo products (realistic Shopify store inventory)
DEMO_STORE_PRODUCTS = [
    {
        "id": "prod_001",
        "title": "Wireless Noise-Cancelling Headphones Pro",
        "description": "Premium 40mm drivers, 30hr battery, foldable design. ANC + Transparency mode.",
        "price": "79.99",
        "vendor": "SoundWave",
        "category": "Electronics",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800",
        "tags": "audio, wireless, premium",
    },
    {
        "id": "prod_002",
        "title": "Organic Ceremonial Matcha Powder",
        "description": "First harvest, stone-ground. Rich umami, vibrant green. 100g resealable pouch.",
        "price": "24.99",
        "vendor": "TeaLeaf Co.",
        "category": "Food & Beverage",
        "image_url": "https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=800",
        "tags": "organic, matcha, wellness",
    },
    {
        "id": "prod_003",
        "title": "Minimalist RFID Leather Wallet",
        "description": "Full-grain leather, holds 8 cards, RFID blocking. Slim 6mm profile.",
        "price": "39.99",
        "vendor": "CraftCo",
        "category": "Accessories",
        "image_url": "https://images.unsplash.com/photo-1627123424574-724758594e93?w=800",
        "tags": "leather, minimalist, wallet",
    },
]

PLATFORM_SPECS = {
    "tiktok":       {"label": "TikTok",           "format": "9:16 · 15s",  "icon": "🎵"},
    "reels":        {"label": "Instagram Reels",  "format": "9:16 · 15s",  "icon": "📸"},
    "youtube":      {"label": "YouTube Short",    "format": "16:9 · 30s",  "icon": "▶️"},
    "amazon":       {"label": "Amazon Listing",   "format": "16:9 · 30s",  "icon": "📦"},
    "product_page": {"label": "Product Page",     "format": "1:1 · 10s",   "icon": "🛍️"},
}


def simulate_shopify_event(product: dict) -> str:
    """Simulate the Shopify webhook event log."""
    return f"""[{time.strftime('%H:%M:%S')}] 🔔 SHOPIFY WEBHOOK RECEIVED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event:   products/create
Store:   cineagentai.myshopify.com
Product: {product['title']}
Price:   ${product['price']}
Vendor:  {product['vendor']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ HMAC signature verified
🚀 ShopReel agent triggered automatically"""


def run_pipeline_sync(product: dict, log_callback, video_callback):
    """Run the real pipeline in a thread, calling callbacks with updates."""
    loop = asyncio.new_event_loop()

    async def _run():
        async for msg in run_demo_pipeline(product):
            if msg.startswith("__VIDEO__"):
                data = json.loads(msg[9:])
                video_callback(data["platform"], data["path"])
            elif msg.startswith("__RESULT__"):
                pass
            else:
                log_callback(msg)

    loop.run_until_complete(_run())
    loop.close()


def generate(product_idx: int):
    """Main demo function — simulates full ShopReel pipeline."""
    product = DEMO_STORE_PRODUCTS[product_idx]

    logs = []
    videos = {p: None for p in PLATFORM_SPECS}
    done = threading.Event()

    def add_log(msg):
        logs.append(msg)

    def set_video(platform, path):
        videos[platform] = path

    # Start pipeline in background
    t = threading.Thread(
        target=run_pipeline_sync,
        args=(product, add_log, set_video),
        daemon=True
    )

    # Step 1: Show Shopify webhook event immediately
    webhook_log = simulate_shopify_event(product)
    yield (
        webhook_log, gr.update(value=product["title"]),
        gr.update(value=f"${product['price']}"),
        gr.update(value=product["vendor"]),
        gr.update(value=product["category"]),
        None, None, None, None, None, ""
    )

    time.sleep(1)
    t.start()

    # Step 2: Stream logs + videos as they arrive
    last_log_len = 0
    while t.is_alive() or len(logs) > last_log_len:
        time.sleep(1.5)
        if len(logs) > last_log_len:
            last_log_len = len(logs)
            full_log = webhook_log + "\n\n" + "\n".join(logs)
            yield (
                full_log,
                gr.update(), gr.update(), gr.update(), gr.update(),
                videos.get("tiktok"), videos.get("reels"),
                videos.get("youtube"), videos.get("amazon"),
                videos.get("product_page"),
                "",
            )
        if not t.is_alive():
            break

    t.join()

    # Final state
    scripts_text = "\n".join([
        f"[{PLATFORM_SPECS[p]['icon']} {PLATFORM_SPECS[p]['label']}]\n{logs[i] if i < len(logs) else ''}"
        for i, p in enumerate(PLATFORM_SPECS)
    ])

    full_log = webhook_log + "\n\n" + "\n".join(logs) + f"\n\n{'━'*40}\n✅ {sum(1 for v in videos.values() if v)} / 5 videos published"

    yield (
        full_log,
        gr.update(), gr.update(), gr.update(), gr.update(),
        videos.get("tiktok"), videos.get("reels"),
        videos.get("youtube"), videos.get("amazon"),
        videos.get("product_page"),
        json.dumps({"product": product["title"], "platforms": list(PLATFORM_SPECS.keys())}, indent=2),
    )


# ── UI ─────────────────────────────────────────────────────────────────────

with gr.Blocks(title="ShopReel") as demo:

    gr.Markdown("""
    # 🛍️ ShopReel — Ecommerce Video Agent
    **Always-on pipeline: New product added → 5 platform videos generated automatically**
    """)

    with gr.Row():
        # Left: Simulated Shopify Store
        with gr.Column(scale=1):
            gr.Markdown("### 🏪 Shopify Store: cineagentai.myshopify.com")
            gr.Markdown("*Select a product to add to your store — ShopReel agent triggers automatically*")

            product_selector = gr.Radio(
                choices=[p["title"] for p in DEMO_STORE_PRODUCTS],
                label="Add Product to Store",
                value=DEMO_STORE_PRODUCTS[0]["title"],
            )
            add_btn = gr.Button("➕ Add Product to Store", variant="primary", size="lg")

            gr.Markdown("---")
            gr.Markdown("**Product Details:**")
            prod_title = gr.Textbox(label="Title", interactive=False)
            with gr.Row():
                prod_price = gr.Textbox(label="Price", interactive=False)
                prod_vendor = gr.Textbox(label="Vendor", interactive=False)
            prod_category = gr.Textbox(label="Category", interactive=False)

        # Right: Agent Pipeline Log
        with gr.Column(scale=2):
            gr.Markdown("### 🤖 ShopReel Agent — Live Reasoning")
            log_out = gr.Textbox(
                lines=18, interactive=False,
                placeholder="Waiting for product to be added to store...\n\nAgent will trigger automatically via Shopify webhook.",
                label="",
            )

    gr.Markdown("### 🎬 Auto-Generated Videos")
    gr.Markdown("*5 platform-optimized videos generated in parallel — ready to publish*")

    with gr.Row():
        tiktok_out = gr.Video(label="🎵 TikTok  9:16 · 15s")
        reels_out = gr.Video(label="📸 Instagram Reels  9:16 · 15s")
        youtube_out = gr.Video(label="▶️ YouTube Short  16:9 · 30s")
    with gr.Row():
        amazon_out = gr.Video(label="📦 Amazon Listing  16:9 · 30s")
        page_out = gr.Video(label="🛍️ Product Page  1:1 · 10s")
        result_out = gr.Code(label="📊 Pipeline Result", language="json")

    # Wire up
    def get_product_idx(title):
        for i, p in enumerate(DEMO_STORE_PRODUCTS):
            if p["title"] == title:
                return i
        return 0

    add_btn.click(
        fn=lambda title: generate(get_product_idx(title)),
        inputs=[product_selector],
        outputs=[log_out, prod_title, prod_price, prod_vendor, prod_category,
                 tiktok_out, reels_out, youtube_out, amazon_out, page_out, result_out],
    )

    gr.Markdown("""
    ---
    **Architecture:** Shopify webhook → Script Agent (Pollinations LLM) → Seedream 5.0 keyframes → Seedance 2.0 I2V (5 parallel) → Quality Agent → edge-tts voiceover → Auto-publish
    
    *Built for [Beta University Seed Agents Challenge](https://betahacks.org) · Track 2: AI-Powered Content Automation*
    """)

if __name__ == "__main__":
    demo.launch(share=True)
