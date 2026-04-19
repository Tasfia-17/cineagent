"""
CineAgent Web UI — Gradio interface for live demo.
Run: python app.py
"""

import gradio as gr
import json
import os
from pipeline import run_pipeline

def generate_film(idea: str, fast_mode: bool):
    if not idea.strip():
        return None, "Please enter a story idea.", ""

    try:
        result = run_pipeline(idea.strip(), output_dir="output", fast_mode=fast_mode)
        screenplay_text = json.dumps(result["screenplay"], indent=2)
        return result["final_video"], f"✅ Film generated: {result['title']}", screenplay_text
    except Exception as e:
        return None, f"❌ Error: {str(e)}", ""


with gr.Blocks(title="CineAgent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎬 CineAgent
    ### One sentence → Cinematic short film with native audio
    *Powered by Seedance 2.0 (ByteDance) · Multi-agent AI pipeline*
    """)

    with gr.Row():
        with gr.Column(scale=2):
            idea_input = gr.Textbox(
                label="Your Story Idea",
                placeholder="A lone astronaut discovers an ancient alien artifact on Mars...",
                lines=3,
            )
            fast_mode = gr.Checkbox(label="Fast mode (480p, quicker generation)", value=True)
            generate_btn = gr.Button("🎬 Generate Film", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("""
            **How it works:**
            1. 📝 Screenplay Agent writes 3-scene script
            2. 🎥 Director Agent enhances visual prompts
            3. 🎞️ Seedance 2.0 generates video clips (parallel)
            4. ✅ Quality Agent scores & retries if needed
            5. 🎙️ Narrator Agent adds voiceover
            6. 🎬 Assembler stitches final film
            """)

    status_output = gr.Textbox(label="Status", interactive=False)

    with gr.Row():
        video_output = gr.Video(label="Generated Film")
        screenplay_output = gr.Code(label="Screenplay (JSON)", language="json")

    generate_btn.click(
        fn=generate_film,
        inputs=[idea_input, fast_mode],
        outputs=[video_output, status_output, screenplay_output],
    )

    gr.Examples(
        examples=[
            ["A lone astronaut discovers an ancient alien artifact on Mars that begins to speak in a forgotten human language.", True],
            ["A street musician in Tokyo plays a melody that makes everyone around them remember their most precious memory.", True],
            ["A deep-sea explorer finds a glowing underwater city that has been hidden for thousands of years.", True],
        ],
        inputs=[idea_input, fast_mode],
    )

if __name__ == "__main__":
    demo.launch(share=True)
