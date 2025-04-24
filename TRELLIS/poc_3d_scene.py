import os
import json
import gradio as gr
from pathlib import Path
import shutil
from datetime import datetime
import logging
from dotenv import load_dotenv
from griptape.structures import Agent
from griptape.drivers.prompt.openai import OpenAiChatPromptDriver
from griptape.memory.structure import ConversationMemory
from griptape.rules import Rule
# os.environ['ATTN_BACKEND'] = 'xformers'   # Can be 'flash-attn' or 'xformers', default is 'flash-attn'
os.environ['SPCONV_ALGO'] = 'native'        # Can be 'native' or 'auto', default is 'auto'.
                                            # 'auto' is faster but will do benchmarking at the beginning.
                                            # Recommended to set to 'native' if run only once.

import imageio
from trellis.pipelines import TrellisTextTo3DPipeline
from trellis.utils import render_utils, postprocessing_utils

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Delete existing prompts.json if it exists
prompts_file = "prompts.json"
if os.path.exists(prompts_file):
    try:
        os.remove(prompts_file)
        logger.info(f"Deleted existing {prompts_file}")
    except Exception as e:
        logger.error(f"Failed to delete {prompts_file}: {e}")

Path("generated_assets").mkdir(parents=True, exist_ok=True)
# Load environment variables
load_dotenv()

# Initialize the agent
try:
    prompt_driver = OpenAiChatPromptDriver(
        model="meta/llama-3.1-8b-instruct",
        base_url="http://localhost:8000/v1",
        api_key="not-needed",
        user="user"
    )
except Exception as e:
    logger.error(f"Failed to initialize prompt driver: {e}")
    raise

conversation_memory = ConversationMemory()

# Create the Agent with updated rules
agent = Agent(
    prompt_driver=prompt_driver,
    rules=[
        Rule("You are a helpful scene planning assistant for 3D content creation."),
        Rule("Your primary task is to assist the user in planning a 3D scene by suggesting objects and layouts."),
        Rule("You must maintain a strict limit of 10 objects in the scene at all times."),
        Rule("When adding new objects, you must remove existing ones to stay within the 10-object limit."),
        Rule("If the user requests more than 10 objects, explain that we need to stay within the limit and ask which objects to remove."),
        Rule("Based on the user's description of a desired scene, propose a list of suitable 3D objects."),
        Rule("Also, provide a basic description of how these objects could be arranged or laid out within the scene."),
        Rule("Explain that you can modify the suggested objects and layout based on their feedback."),
        Rule("Acknowledge that the goal is eventually to generate text prompts for 3D modeling tools like TRELLIS."),
        Rule("Keep your initial response concise and focused on the object list and layout description."),
        Rule("When receiving feedback, clearly indicate what changes you're making to the scene."),
        Rule("After each modification, ask if the user would like to make any further adjustments."),
        Rule("Always list the current objects in the scene and confirm the total count is 10 or less."),
        Rule("When generating 3D prompts, focus on key visual and physical characteristics of each object."),
        Rule("For each object, include details about its shape, size, materials, and surface properties."),
        Rule("Incorporate the object's context and relationship to other objects in the scene."),
        Rule("Keep each object's prompt to exactly 40 words or less for optimal generation quality."),
        Rule("Use descriptive adjectives and specific material terms to enhance the 3D generation."),
        Rule("When the scene is finalized, generate a separate prompt for each object in the scene.")
    ]
)

agent.memory = conversation_memory

# Load TRELLIS pipeline
os.environ['SPCONV_ALGO'] = 'native'
#pipeline = TrellisTextTo3DPipeline.from_pretrained("JeffreyXiang/TRELLIS-text-base")
pipeline = TrellisTextTo3DPipeline.from_pretrained("JeffreyXiang/TRELLIS-text-large")
pipeline.cuda()

def save_prompts_to_json(scene_name, object_prompts, initial_description=None):
    """Save prompts to a JSON file in a structured format."""
    try:
        prompts_file = "prompts.json"
        
        # Create the data structure
        new_scene = {
            "name": scene_name,
            "description": initial_description,
            "objects": [
                {"name": name, "prompt": prompt}
                for name, prompt in object_prompts.items()
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        # Read existing data if file exists
        if os.path.exists(prompts_file):
            with open(prompts_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"scenes": []}
        
        # Add new scene
        data["scenes"].append(new_scene)
        
        # Save updated data
        with open(prompts_file, 'w') as f:
            json.dump(data, f, indent=4)
        
        logger.info(f"Successfully saved prompts to {prompts_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to save prompts: {e}")
        return False

def generate_3d_prompts(scene_name, initial_description):
    """Generate 3D prompts for each object in the final scene."""
    try:
        generation_prompt = f"""Generate detailed 3D prompts for each object in the current scene, focusing on:
        1. Visual and physical characteristics
        2. Materials and surface properties
        3. Context within the scene
        Keep each prompt to exactly 40 words or less.
        Format each object's prompt with 'Object:' and 'Prompt:' labels.
        Scene description: {initial_description}"""
        
        response = agent.run(generation_prompt)
        
        response_text = response.output.value if hasattr(response, 'output') else str(response)
        logger.info("Received response from agent")
        
        object_prompts = {}
        current_object = None
        current_prompt = []
        
        for line in response_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if 'Object:' in line:
                if current_object and current_prompt:
                    prompt_text = ' '.join(current_prompt)
                    word_count = len(prompt_text.split())
                    if word_count > 40:
                        prompt_text = ' '.join(prompt_text.split()[:40])
                    object_prompts[current_object] = prompt_text
                current_object = line.split('Object:')[-1].strip().strip('*').strip()
                current_prompt = []
            elif 'Prompt:' in line:
                prompt_text = line.split('Prompt:')[-1].strip().strip('*').strip()
                current_prompt.append(prompt_text)
        
        if current_object and current_prompt:
            prompt_text = ' '.join(current_prompt)
            word_count = len(prompt_text.split())
            if word_count > 40:
                prompt_text = ' '.join(prompt_text.split()[:40])
            object_prompts[current_object] = prompt_text
        
        if not object_prompts:
            logger.warning("No prompts were extracted from the response")
            return False, None, generation_prompt
        
        if not save_prompts_to_json(scene_name, object_prompts, initial_description):
            return False, None, generation_prompt
        
        return True, object_prompts, generation_prompt
    except Exception as e:
        logger.error(f"Error generating prompts: {e}")
        return False, None, generation_prompt

def generate_scene_name(description):
    """Generate a scene name from the description."""
    try:
        response = agent.run(f"""Based on this scene description: "{description}"
        Generate a short, descriptive name for this scene (2-3 words).
        Format the response as: "Scene Name: [name]"
        """)
        
        response_text = response.output.value if hasattr(response, 'output') else str(response)
        
        for line in response_text.split('\n'):
            if 'Scene Name:' in line:
                return line.split('Scene Name:')[-1].strip()
        
        return f"scene_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    except Exception as e:
        logger.error(f"Error generating scene name: {e}")
        return f"scene_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def chat_with_agent(message, history):
    """Handle chat interaction with the agent."""
    try:
        response = agent.run(message)
        response_text = response.output.value if hasattr(response, 'output') else str(response)
        return response_text
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return f"An error occurred: {str(e)}"

def generate_assets(scene_name, object_name, prompt, output_dir, seed, sparse_steps, slat_steps):
    """Generate 3D assets for a single object."""
    try:
        outputs = pipeline.run(
            prompt,
            seed=seed,
            sparse_structure_sampler_params={
                "steps": sparse_steps,
                "cfg_strength": 7.0,
            },
            slat_sampler_params={
                "steps": slat_steps,
                "cfg_strength": 7.0,
            },
        )
        
        base_filename = f"{scene_name}_{object_name}"
        base_path = os.path.join(output_dir, base_filename)
        
        glb = postprocessing_utils.to_glb(
            outputs['gaussian'][0],
            outputs['mesh'][0],
            simplify=0.95,
            texture_size=1024,
        )
        glb_path = f"{base_path}.glb"
        glb.export(glb_path)
        
        return True, f"Successfully generated assets for {object_name}", glb_path
    except Exception as e:
        return False, f"Error generating assets for {object_name}: {str(e)}", None

def process_scene(scene_data, output_dir, progress, seed, sparse_steps, slat_steps):
    """Process all objects in a scene."""
    scene_name = scene_data['name']
    results = [f"Processing scene: {scene_name}"]
    generated_assets = []
    
    total_objects = len(scene_data['objects'])
    for i, obj in enumerate(scene_data['objects'], 1):
        progress((i-1)/total_objects, desc=f"Generating {obj['name']}...")
        success, message, glb_path = generate_assets(
            scene_name,
            obj['name'],
            obj['prompt'],
            output_dir,
            seed,
            sparse_steps,
            slat_steps
        )
        results.append(message)
        if success and glb_path:
            generated_assets.append(glb_path)
        progress(i/total_objects, desc=f"Completed {obj['name']}")
    
    if generated_assets:
        results.append("\nGenerated assets in this scene:")
        for asset_path in generated_assets:
            results.append(f"- {asset_path}")
    
    return results

def generate_all_assets(prompts_file, output_dir, delete_existing, seed, sparse_steps, slat_steps, progress=gr.Progress()):
    """Generate assets for all scenes in the prompts file."""
    try:
        if delete_existing and os.path.exists(output_dir):
            progress(0, desc="Deleting existing output directory...")
            shutil.rmtree(output_dir)
            progress(0.1, desc="Output directory deleted")
        
        os.makedirs(output_dir, exist_ok=True)
        
        with open(prompts_file, 'r') as f:
            data = json.load(f)
        
        all_results = []
        total_scenes = len(data['scenes'])
        
        for i, scene in enumerate(data['scenes'], 1):
            progress(i/total_scenes, desc=f"Processing scene {i}/{total_scenes}")
            results = process_scene(scene, output_dir, progress, seed, sparse_steps, slat_steps)
            all_results.extend(results)
            progress(i/total_scenes, desc=f"Completed scene {i}/{total_scenes}")
        
        all_results.append("\n=== Summary of Generated Assets ===")
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.glb'):
                    all_results.append(f"- {os.path.join(root, file)}")
        
        return "\n".join(all_results)
    except Exception as e:
        return f"Error processing prompts file: {str(e)}"

# Create Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# 3D Scene Generator POC")
    
    with gr.Tabs():
        with gr.TabItem("Chat & Generate Prompts"):
            with gr.Row():
                with gr.Column():
                    chatbot = gr.Chatbot(
                        height=400,
                        value=[("Assistant", "Hello! I'm your helpful scene planning assistant. Please describe the scene you'd like to create.")]
                    )
                    msg = gr.Textbox(label="Your message", placeholder="Describe your scene...")
                    submit_btn = gr.Button("Send")
                    clear_btn = gr.Button("Clear Chat")
                    
                    def clear_chat():
                        agent.memory = ConversationMemory()
                        return [("Assistant", "Hello! I'm your helpful scene planning assistant. Please describe the scene you'd like to create.")]
                    
                    clear_btn.click(clear_chat, outputs=chatbot)
                    
                    def respond(message, chat_history):
                        response = chat_with_agent(message, chat_history)
                        chat_history.append((message, response))
                        return chat_history, ""
                    
                    submit_btn.click(respond, [msg, chatbot], [chatbot, msg])
                    msg.submit(respond, [msg, chatbot], [chatbot, msg])
                    
                    with gr.Row():
                        confirm_objects_btn = gr.Button("Confirm Objects List")
                        generate_prompts_btn = gr.Button("Generate 3D Prompts")
                    
                    prompts_output = gr.Textbox(label="Generated Prompts", lines=10)
                    generation_prompt_display = gr.Textbox(label="Generation Prompt Used", lines=5, interactive=False)
                    
                    def on_confirm_objects(chat_history):
                        if not chat_history or len(chat_history) == 1:
                            return "Please describe your scene first!"
                        
                        response = agent.run("""Please list all the current objects in the scene and ask the user if they are happy with this list.
                        If they are happy, they can click the 'Generate 3D Prompts' button to proceed.""")
                        response_text = response.output.value if hasattr(response, 'output') else str(response)
                        chat_history.append(("Assistant", response_text))
                        return chat_history
                    
                    def on_generate_prompts(chat_history):
                        if not chat_history or len(chat_history) == 1:
                            return "Please describe your scene first!", ""
                        
                        # Get the last user message as scene description
                        scene_description = chat_history[-1][0]
                        scene_name = generate_scene_name(scene_description)
                        success, prompts, gen_prompt = generate_3d_prompts(scene_name, scene_description)
                        
                        if success:
                            output = f"Scene Name: {scene_name}\n\nGenerated Prompts:\n"
                            for obj, prompt in prompts.items():
                                output += f"\nObject: {obj}\nPrompt: {prompt}\n"
                            return output, gen_prompt
                        else:
                            return "Failed to generate prompts. Please try again.", ""
                    
                    confirm_objects_btn.click(on_confirm_objects, [chatbot], [chatbot])
                    generate_prompts_btn.click(on_generate_prompts, [chatbot], [prompts_output, generation_prompt_display])
        
        with gr.TabItem("Generate 3D Assets"):
            with gr.Row():
                prompts_file = gr.Textbox(
                    label="Prompts JSON File",
                    value="prompts.json",
                    interactive=True
                )
                output_dir = gr.Textbox(
                    label="Output Directory",
                    value="generated_assets",
                    interactive=True
                )
            
            with gr.Row():
                seed = gr.Number(
                    label="Random Seed",
                    value=42,
                    interactive=True
                )
                sparse_steps = gr.Number(
                    label="Sparse Structure Steps",
                    value=25,
                    interactive=True
                )
                slat_steps = gr.Number(
                    label="Slat Sampler Steps",
                    value=25,
                    interactive=True
                )
            
            delete_existing = gr.Checkbox(
                label="Delete existing output directory",
                value=True
            )
            
            generate_btn = gr.Button("Generate Assets")
            output = gr.Textbox(label="Generation Progress", lines=10)
            
            generate_btn.click(
                generate_all_assets,
                inputs=[prompts_file, output_dir, delete_existing, seed, sparse_steps, slat_steps],
                outputs=output
            )

if __name__ == "__main__":
    demo.launch()