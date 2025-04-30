# 3D Scene Generator POC

This is a proof-of-concept implementation of a 3D scene generator using TRELLIS.

## Features

- Interactive chat interface for scene planning
- Automatic 3D prompt generation
- 3D asset generation using TRELLIS
- Process termination for VRAM management

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python run.py
```

2. Use the Gradio interface to:
   - Chat with the scene planner
   - Generate 3D prompts
   - Generate 3D assets

3. To terminate the application and free VRAM:
```bash
python terminator.py
```
This will:
- Gracefully terminate the Gradio application
- Free up GPU memory
- Allow you to proceed with other operations (e.g., Blender)

## Directory Structure

- `agent.py`: Scene planning agent implementation
- `generator.py`: 3D asset generation using TRELLIS
- `interface.py`: Gradio interface implementation
- `terminator.py`: Process termination utility
- `utils.py`: Utility functions
- `config.py`: Configuration settings
- `run.py`: Main entry point

## Notes

- The application uses a TCP server for process termination
- VRAM is automatically freed when the process is terminated
- The terminator uses SIGTERM for graceful shutdown and SIGKILL as a fallback 