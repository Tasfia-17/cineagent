"""
ShopReel UI — Gradio demo interface
"""

import gradio as gr
import json
import asyncio
import threading
from shopreel_pipeline import run_shopreel_streaming

DEMO_PRODUCTS = [
    ["Wireless Noise-Cancelling Headphones", "Premium sound, 30hr battery, foldable design.", "79.99", "SoundWave", ""],
    ["Organic Matcha Green Tea Powder", "Ceremonial grade, 100g. Rich umami flavor, antioxidants.", "24.99", "TeaLeaf", ""],
    ["Minimalist Leather Wallet", "Slim RFID-blocking wallet, holds 8 cards. Full-grain leather.", "39.99", "CraftCo", ""],
]


def generate_videos(title, description, price, vendor, image_url):
    """Sync generator — yields UI updates as pipeline runs."""
    if not title.strip():
        yield "Please enter a product title.", None, None, None, None, None, ""
        return

    product = {
        "title": title,
        "body_html": description,
        "vendor": vendor,
        "image_url": image_url,
        "variants": [{"price": price}] if price else [],
    }

    log_lines = []
    videos = {}
    scripts = {}

    # Run async pipeline in a new event loop
    loop = asyncio.new_event_loop()

    async def collect():
        async for msg in run_shopreel_streaming(product):
            if msg.startswith("__RESULT__"):
                result = json.loads(msg[10:])
                videos.update(result.get("videos", {}))
                scripts.update(result.get("scripts", {}))
            else:
                log_lines.append(msg)

    # Run in thread to avoid blocking Gradio
    result_ready = threading.Event()

    def run_loop():
        loop.run_until_complete(collect())
        result_ready.set()

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()

    # Poll and yield updates every 2 seconds
    import time
    last_len = 0
    while not result_ready.is_set():
        time.sleep(2)
        if len(log_lines) > last_len:
            last_len = len(log_lines)
            yield (
                "\n".join(log_lines),
                videos.get("tiktok"), videos.get("reels"),
                videos.get("youtube"), videos.get("amazon"),
                videos.get("product_page"),
                "",
            )

    t.join()
    loop.close()

    yield (
        "\n".join(log_lines) + "\n\n✅ Done!",
        videos.get("tiktok"), videos.get("reels"),
        videos.get("youtube"), videos.get("amazon"),
        videos.get("product_page"),
        json.dumps(scripts, indent=2),
    )


with gr.Blocks(title="ShopReel", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🛍️ ShopReel
    ### Product → 5 platform videos automatically
    *Seedance 2.0 · Seedream 5.0 · Multi-agent pipeline*
    """)

    with gr.Row():
        with gr.Column(scale=2):
            title_in = gr.Textbox(label="Product Title", placeholder="Wireless Noise-Cancelling Headphones")
            desc_in = gr.Textbox(label="Description", lines=2, placeholder="Premium sound, 30hr battery...")
            with gr.Row():
                price_in = gr.Textbox(label="Price ($)", placeholder="79.99")
                vendor_in = gr.Textbox(label="Brand", placeholder="SoundWave")
            image_in = gr.Textbox(label="Product Image URL (optional)")
            generate_btn = gr.Button("🎬 Generate 5 Videos", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("""
            **Pipeline:**
            1. 📝 Script Agent → 5 platform scripts
            2. 🖼️ Seedream 5.0 → keyframe per platform
            3. 🎞️ Seedance 2.0 I2V → 5 videos (parallel)
            4. ✅ Quality Agent → score + retry
            5. 🎙️ Narrator → voiceover
            """)

    log_out = gr.Textbox(label="🤖 Live Agent Reasoning", lines=12, interactive=False)

    gr.Markdown("### 🎬 Generated Videos")
    with gr.Row():
        tiktok_out = gr.Video(label="TikTok (9:16)")
        reels_out = gr.Video(label="Instagram Reels (9:16)")
        youtube_out = gr.Video(label="YouTube Short (16:9)")
    with gr.Row():
        amazon_out = gr.Video(label="Amazon Listing (16:9)")
        page_out = gr.Video(label="Product Page (1:1)")
        scripts_out = gr.Code(label="📄 Scripts", language="json")

    generate_btn.click(
        fn=generate_videos,
        inputs=[title_in, desc_in, price_in, vendor_in, image_in],
        outputs=[log_out, tiktok_out, reels_out, youtube_out, amazon_out, page_out, scripts_out],
    )

    gr.Examples(
        examples=DEMO_PRODUCTS,
        inputs=[title_in, desc_in, price_in, vendor_in, image_in],
        label="Demo Products",
    )

if __name__ == "__main__":
    demo.launch(share=True)
