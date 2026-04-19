"""
CineAgent Web UI — Gradio interface with live streaming agent logs.
Run: python app.py
"""

import gradio as gr
import json
import asyncio
from pipeline import run_pipeline_streaming


async def generate_film(idea: str, fast_mode: bool):
    if not idea.strip():
        yield "Please enter a story idea.", None, ""
        return

    log_lines = []
    final_video = None
    screenplay_text = ""

    async for msg in run_pipeline_streaming(idea.strip(), output_dir="output", fast=fast_mode):
        if msg.startswith("__RESULT__"):
            result = json.loads(msg[10:])
            final_video = result.get("final_video", "")
            screenplay_text = json.dumps(result.get("screenplay", {}), indent=2)
        else:
            log_lines.append(msg)
            yield "\n".join(log_lines), None, ""

    yield "\n".join(log_lines), final_video, screenplay_text


with gr.Blocks(title="CineAgent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎬 CineAgent
    ### One sentence → Cinematic short film with native audio
    *Seedance 2.0 (video) · Seedream 5.0 (keyframes) · Multi-agent pipeline*
    """)

    with gr.Row():
        with gr.Column(scale=2):
            idea_input = gr.Textbox(
                label="Your Story Idea",
                placeholder="A lone astronaut discovers an ancient alien artifact on Mars...",
                lines=3,
            )
            fast_mode = gr.Checkbox(label="Fast mode (480p)", value=True)
            generate_btn = gr.Button("🎬 Generate Film", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("""
            **Agent Pipeline:**
            1. 📝 Screenplay Agent → 3-scene script
            2. 🎥 Director Agent → storyboard prompts
            3. 🖼️ Seedream 5.0 → keyframe per scene
            4. 🎞️ Seedance 2.0 I2V → video clips (parallel)
            5. ✅ Quality Agent → score + auto-retry
            6. 🎙️ Narrator → edge-tts voiceover
            7. 🎬 Assembler → final film
            """)

    # Live agent log — this is the "show reasoning" panel judges want to see
    log_output = gr.Textbox(
        label="🤖 Live Agent Reasoning",
        lines=15,
        interactive=False,
        placeholder="Agent logs will appear here in real-time...",
    )

    with gr.Row():
        video_output = gr.Video(label="🎬 Generated Film")
        screenplay_output = gr.Code(label="📄 Screenplay", language="json")

    generate_btn.click(
        fn=generate_film,
        inputs=[idea_input, fast_mode],
        outputs=[log_output, video_output, screenplay_output],
    )

    gr.Examples(
        examples=[
            ["A lone astronaut discovers an ancient alien artifact on Mars that begins to speak in a forgotten human language.", True],
            ["A street musician in Tokyo plays a melody that makes everyone around them remember their most precious memory.", True],
            ["A deep-sea explorer finds a glowing underwater city hidden for thousands of years.", True],
        ],
        inputs=[idea_input, fast_mode],
    )

if __name__ == "__main__":
    demo.launch(share=True)
