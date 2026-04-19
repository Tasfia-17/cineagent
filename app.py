"""
ShopReel UI — Gradio demo interface
Shows live agent reasoning + 5 platform videos side by side
"""

import gradio as gr
import json
import asyncio
from shopreel_pipeline import run_shopreel_streaming

DEMO_PRODUCTS = [
    {"title": "Wireless Noise-Cancelling Headphones", "description": "Premium sound, 30hr battery, foldable design. Perfect for travel and work.", "price": "79.99", "vendor": "SoundWave", "image_url": ""},
    {"title": "Organic Matcha Green Tea Powder", "description": "Ceremonial grade, 100g. Rich umami flavor, packed with antioxidants.", "price": "24.99", "vendor": "TeaLeaf", "image_url": ""},
    {"title": "Minimalist Leather Wallet", "description": "Slim RFID-blocking wallet, holds 8 cards. Full-grain leather.", "price": "39.99", "vendor": "CraftCo", "image_url": ""},
]


async def generate_videos(title, description, price, vendor, image_url):
    if not title.strip():
        yield "Please enter a product title.", None, None, None, None, None, ""
        return

    product = {
        "title": title, "body_html": description,
        "vendor": vendor, "image_url": image_url,
        "variants": [{"price": price}] if price else [],
    }

    log_lines = []
    videos = {}
    scripts = {}

    async for msg in run_shopreel_streaming(product):
        if msg.startswith("__RESULT__"):
            result = json.loads(msg[10:])
            videos = result.get("videos", {})
            scripts = result.get("scripts", {})
        else:
            log_lines.append(msg)
            yield (
                "\n".join(log_lines),
                videos.get("tiktok"), videos.get("reels"),
                videos.get("youtube"), videos.get("amazon"),
                videos.get("product_page"),
                "",
            )

    scripts_text = json.dumps(scripts, indent=2)
    yield (
        "\n".join(log_lines) + "\n\n✅ All done!",
        videos.get("tiktok"), videos.get("reels"),
        videos.get("youtube"), videos.get("amazon"),
        videos.get("product_page"),
        scripts_text,
    )


with gr.Blocks(title="ShopReel", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🛍️ ShopReel
    ### Add a product → 5 platform-optimized videos in minutes
    *Seedance 2.0 · Seedream 5.0 · Always-on ecommerce video agent*
    """)

    with gr.Row():
        with gr.Column(scale=2):
            title_in = gr.Textbox(label="Product Title", placeholder="Wireless Noise-Cancelling Headphones")
            desc_in = gr.Textbox(label="Description", lines=2, placeholder="Premium sound, 30hr battery...")
            with gr.Row():
                price_in = gr.Textbox(label="Price ($)", placeholder="79.99")
                vendor_in = gr.Textbox(label="Brand", placeholder="SoundWave")
            image_in = gr.Textbox(label="Product Image URL (optional)", placeholder="https://...")
            generate_btn = gr.Button("🎬 Generate 5 Videos", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("""
            **Agent Pipeline:**
            1. 📝 Script Agent → 5 platform scripts (Pollinations LLM)
            2. 🖼️ Seedream 5.0 → product keyframe per platform
            3. 🎞️ Seedance 2.0 I2V → 5 videos in parallel
            4. ✅ Quality Agent → hook strength + CTA score
            5. 🎙️ Narrator → platform-optimized voiceover

            **Platforms:**
            - TikTok (9:16, 15s)
            - Instagram Reels (9:16, 15s)
            - YouTube Short (16:9, 30s)
            - Amazon Listing (16:9, 30s)
            - Product Page (1:1, 10s)
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
        examples=[[p["title"], p["description"], p["price"], p["vendor"], p["image_url"]] for p in DEMO_PRODUCTS],
        inputs=[title_in, desc_in, price_in, vendor_in, image_in],
        label="Demo Products",
    )

if __name__ == "__main__":
    demo.launch(share=True)
