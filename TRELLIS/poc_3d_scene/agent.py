import logging
from datetime import datetime
from griptape.structures import Agent
from griptape.drivers.prompt.openai import OpenAiChatPromptDriver
from griptape.memory.structure import ConversationMemory
from griptape.rules import Rule
from config import AGENT_MODEL, AGENT_BASE_URL, LOG_LEVEL, LOG_FORMAT
from utils import save_prompts_to_json

# Set up logging
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


class ScenePlanningAgent:
    def __init__(self):
        self.memory = ConversationMemory()
        self.agent = self._initialize_agent()
        self.is_generating_prompts = False

    def _get_planning_rules(self):
        """Get rules for scene planning phase."""
        return [
            Rule(
                "You are a helpful scene planning assistant for 3D content creation."
            ),
            Rule(
                "Your primary task is to assist the user in planning a 3D scene by suggesting objects and layouts."
            ),
            Rule(
                "You must maintain a strict limit of 10 objects in the scene at all times."
            ),
            Rule(
                "When adding new objects, you must remove existing ones to stay within the 10-object limit."
            ),
            Rule(
                "If the user requests more than 10 objects, explain that we need to stay within the limit and ask which objects to remove."
            ),
            Rule(
                "Based on the user's description of a desired scene, propose a list of suitable 3D objects."
            ),
            Rule(
                "Also, provide a basic description of how these objects could be arranged or laid out within the scene."
            ),
            Rule(
                "Explain that you can modify the suggested objects and layout based on their feedback."
            ),
            Rule(
                "Acknowledge that the goal is eventually to generate text prompts for 3D modeling tools like TRELLIS."
            ),
            Rule(
                "Keep your initial response concise and focused on the object list and layout description."
            ),
            Rule(
                "When receiving feedback, clearly indicate what changes you're making to the scene."
            ),
            Rule(
                "After each modification, ask if the user would like to make any further adjustments."
            ),
            Rule(
                "Always list the current objects in the scene and confirm the total count is 10 or less."
            ),
            Rule(
                "When the user is satisfied with the scene, tell them they can click the 'Generate 3D Prompts' button to create 3D prompts."
            ),
            Rule(
                "If the user asks to generate 3D prompts in chat, remind them to use the 'Generate 3D Prompts' button instead. Your role is only to help plan and modify the scene."
            ),
            Rule(
                "DO NOT describe the visual or physical characteristics of objects during the planning phase."
            ),
            Rule(
                "DO NOT discuss materials, textures, or surface properties during the planning phase."
            ),
            Rule(
                "Focus only on object names and their spatial arrangement during the planning phase."
            ),
            # Rule(
            #     "Save detailed object descriptions for the 3D prompt generation phase."
            # ),
            Rule(
                "When the user asks to edit or modify items in the scene, only update the object list and layout. Do not generate prompts or switch to generation mode."
            ),
        ]

    def _get_prompt_generation_rules(self):
        """Get rules for 3D prompt generation phase."""
        return [
            Rule(
                "You are now in 3D prompt generation mode. Your task is to create detailed prompts for each object in the scene."
            ),
            Rule(
                "For each object, focus on key visual and physical characteristics."
            ),
            Rule(
                "Include details about the object's shape, size, materials, and surface properties."
            ),
            Rule(
                "Incorporate the object's context and relationship to other objects in the scene."
            ),
            Rule(
                "Keep each object's prompt to exactly 40 words or less for optimal generation quality."
            ),
            Rule(
                "Use descriptive adjectives and specific material terms to enhance the 3D generation."
            ),
            Rule(
                "Generate a separate prompt for each object in the scene."
            ),
            Rule(
                "Format each object's prompt with 'Object:' and 'Prompt:' labels."
            ),
        ]

    def _initialize_agent(self):
        """Initialize the agent with initial planning rules."""
        try:
            prompt_driver = OpenAiChatPromptDriver(
                model=AGENT_MODEL,
                base_url=AGENT_BASE_URL,
                api_key="not-needed",
                user="user",
            )
        except Exception as e:
            logger.error(f"Failed to initialize prompt driver: {e}")
            raise

        agent = Agent(
            prompt_driver=prompt_driver,
            rules=self._get_planning_rules(),
        )
        agent.memory = self.memory
        return agent

    def chat(self, message):
        """Handle chat messages and provide scene planning assistance."""
        try:
            # Always ensure we're in planning mode
            if self.is_generating_prompts:
                self.agent.rules = self._get_planning_rules()
                self.is_generating_prompts = False

            # Normal chat response - always in planning mode
            self.agent.rules = self._get_planning_rules()
            response = self.agent.run(message)
            response_text = response.output.value if hasattr(response, "output") else str(response)
            return response_text
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return f"An error occurred: {str(e)}"

    def generate_scene_name(self, description):
        """Generate a scene name from the description."""
        try:
            # response = self.agent.run(f"""Based on this scene description: "{description}"
            # Generate a short, descriptive name for this scene (2-3 words).
            # Format the response as: "Scene Name: [name]"
            # """)

            response = self.agent.run(f"""Based on this scene discussion,
            Generate a short, descriptive name for this scene (2-3 words).
            Format the response as: "Scene Name: [name]"
            """)

            response_text = (
                response.output.value if hasattr(response, "output") else str(response)
            )

            for line in response_text.split("\n"):
                if "Scene Name:" in line:
                    return line.split("Scene Name:")[-1].strip()

            return f"scene_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        except Exception as e:
            logger.error(f"Error generating scene name: {e}")
            return f"scene_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def generate_3d_prompts(self, scene_name, initial_description):
        """Generate 3D prompts for each object in the final scene."""
        try:
            logger.info("Switching to prompt generation mode")
            # Switch to prompt generation mode
            self.agent.rules = self._get_prompt_generation_rules()
            self.is_generating_prompts = True

            generation_prompt = f"""Generate detailed 3D prompts for each object in the current scene, focusing on:
            1. Visual and physical characteristics
            2. Materials and surface properties
            3. Context within the scene
            Generate prompt for each object confirmed by the user in this list: {initial_description}
            Keep each prompt to exactly 40 words or less.
            Format each object's prompt with 'Object:' and 'Prompt:' labels.
            """

            response = self.agent.run(generation_prompt)

            response_text = (
                response.output.value if hasattr(response, "output") else str(response)
            )
            logger.info("Received response from agent")

            object_prompts = {}
            current_object = None
            current_prompt = []

            for curr_line in response_text.split("\n"):
                line = curr_line.strip()
                if not line:
                    continue

                if "Object:" in line:
                    if current_object and current_prompt:
                        prompt_text = " ".join(current_prompt)
                        word_count = len(prompt_text.split())
                        if word_count > 40:
                            prompt_text = " ".join(prompt_text.split()[:40])
                        object_prompts[current_object] = prompt_text
                    current_object = (
                        line.split("Object:")[-1].strip().strip("*").strip()
                    )
                    current_prompt = []
                elif "Prompt:" in line:
                    prompt_text = line.split("Prompt:")[-1].strip().strip("*").strip()
                    current_prompt.append(prompt_text)

            if current_object and current_prompt:
                prompt_text = " ".join(current_prompt)
                word_count = len(prompt_text.split())
                if word_count > 40:
                    prompt_text = " ".join(prompt_text.split()[:40])
                object_prompts[current_object] = prompt_text

            if not object_prompts:
                logger.warning("No prompts were extracted from the response")
                return False, None, generation_prompt

            if not save_prompts_to_json(
                scene_name, object_prompts, initial_description
            ):
                return False, None, generation_prompt

            return True, object_prompts, generation_prompt
        except Exception as e:
            logger.error(f"Error generating prompts: {e}")
            return False, None, generation_prompt
        finally:
            # Always switch back to planning mode after generation
            logger.info("Switching back to planning mode after generation")
            self.agent.rules = self._get_planning_rules()
            self.is_generating_prompts = False
            

    def clear_memory(self):
        """Clear conversation memory."""
        self.memory = ConversationMemory()
        self.agent.memory = self.memory
        # Reinitialize the agent to get a fresh context
        self.agent = self._initialize_agent()
