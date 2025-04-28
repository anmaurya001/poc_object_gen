import gradio as gr
from agent import ScenePlanningAgent
from generator import AssetGenerator
from utils import delete_prompts_file
from config import (
    DEFAULT_SEED,
    DEFAULT_SPARSE_STEPS,
    DEFAULT_SLAT_STEPS,
    OUTPUT_DIR,
    PROMPTS_FILE,
    INITIAL_MESSAGE,
)


class SceneGeneratorInterface:
    def __init__(self):
        self.agent = ScenePlanningAgent()
        self.generator = AssetGenerator()
        self.INITIAL_MESSAGE = INITIAL_MESSAGE
        # Delete existing prompts file if it exists
        delete_prompts_file()

    def create_interface(self):
        """Create the Gradio interface for the 3D Scene Generator."""
        with gr.Blocks() as demo:
            gr.Markdown("# 3D Scene Generator POC")

            with gr.Tabs():
                with gr.TabItem("Chat & Generate Prompts"):
                    with gr.Row():
                        with gr.Column():
                            chatbot = gr.Chatbot(
                                height=400, value=[(None, self.INITIAL_MESSAGE)]
                            )
                            msg = gr.Textbox(
                                label="Your message",
                                placeholder="Describe your scene...",
                            )
                            submit_btn = gr.Button("Send")
                            clear_btn = gr.Button("Clear Chat")

                            def clear_chat():
                                # Clear agent's memory
                                self.agent.clear_memory()
                                # Reset chat display to initial message
                                return [(None, self.INITIAL_MESSAGE)]

                            clear_btn.click(clear_chat, outputs=chatbot)

                            def respond(message, chat_history):
                                response = self.agent.chat(message)
                                # First element is user message, second is assistant response
                                chat_history.append((message, response))
                                return chat_history, ""

                            submit_btn.click(respond, [msg, chatbot], [chatbot, msg])
                            msg.submit(respond, [msg, chatbot], [chatbot, msg])

                            gr.Markdown("""
                            ### Ready to Generate 3D Prompts?
                            When you're satisfied with your scene, click the 'Generate 3D Prompts' button below to create detailed 3D prompts for each object.
                            """)
                            
                            generate_prompts_btn = gr.Button("Generate 3D Prompts")

                            prompts_output = gr.Textbox(
                                label="Generated Prompts", 
                                lines=10,
                                show_copy_button=True
                            )
                            generation_prompt_display = gr.Textbox(
                                label="Generation Prompt Used",
                                lines=5,
                                interactive=False,
                            )

                            def on_generate_prompts(chat_history):
                                if not chat_history or len(chat_history) == 1:
                                    return "Please describe your scene first!", ""

                                # Get the last message
                                last_user_message, last_assistant_response = chat_history[-1]

                                scene_name = self.agent.generate_scene_name(
                                    last_assistant_response
                                )
                                success, prompts, gen_prompt = (
                                    self.agent.generate_3d_prompts(
                                        scene_name, last_assistant_response
                                    )
                                )

                                if success:
                                    output = f"Scene Name: {scene_name}\n\nGenerated Prompts:\n"
                                    for obj, prompt in prompts.items():
                                        output += f"\nObject: {obj}\nPrompt: {prompt}\n"
                                    return output, gen_prompt
                                else:
                                    return (
                                        "Failed to generate prompts. Please try again.",
                                        "",
                                    )

                            generate_prompts_btn.click(
                                on_generate_prompts,
                                [chatbot],
                                [prompts_output, generation_prompt_display],
                            )

                with gr.TabItem("Generate 3D Assets"):
                    with gr.Row():
                        prompts_file = gr.Textbox(
                            label="Prompts JSON File",
                            value=str(PROMPTS_FILE),
                            interactive=True,
                        )
                        output_dir = gr.Textbox(
                            label="Output Directory",
                            value=str(OUTPUT_DIR),
                            interactive=True,
                        )

                    with gr.Row():
                        seed = gr.Number(
                            label="Random Seed", value=DEFAULT_SEED, interactive=True
                        )
                        sparse_steps = gr.Number(
                            label="Sparse Structure Steps",
                            value=DEFAULT_SPARSE_STEPS,
                            interactive=True,
                        )
                        slat_steps = gr.Number(
                            label="Slat Sampler Steps",
                            value=DEFAULT_SLAT_STEPS,
                            interactive=True,
                        )

                    delete_existing = gr.Checkbox(
                        label="Delete existing output directory", value=True
                    )

                    generate_btn = gr.Button("Generate Assets")
                    output = gr.Textbox(label="Generation Progress", lines=10)

                    def generate_assets_with_progress(prompts_file, output_dir, delete_existing, seed, sparse_steps, slat_steps):
                        return self.generator.generate_all_assets(
                            prompts_file,
                            output_dir,
                            delete_existing,
                            seed,
                            sparse_steps,
                            slat_steps,
                            progress=gr.Progress()
                        )

                    generate_btn.click(
                        generate_assets_with_progress,
                        inputs=[
                            prompts_file,
                            output_dir,
                            delete_existing,
                            seed,
                            sparse_steps,
                            slat_steps,
                        ],
                        outputs=output
                    )

        return demo

    def launch(self, **kwargs):
        """Launch the Gradio interface."""
        demo = self.create_interface()
        demo.launch(**kwargs)
