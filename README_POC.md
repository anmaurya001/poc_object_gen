# POC 3D Scene Generator

A proof-of-concept application that combines natural language processing with 3D asset generation using TRELLIS.

## Features

- Interactive chat interface for scene planning
- AI-assisted object suggestion and layout
- Automatic 3D asset generation from text prompts
- Blender auto-import functionality for generated assets
- VRAM management with process termination

## Prerequisites

### Windows Installation (Required for TRELLIS) - [TRELLIS Windows Installation Guide](https://github.com/ericcraft-mh/TRELLIS-install-windows) for Windows setup instructions

Before installing this project, you need to set up the development environment on Windows:

1. Install Visual Studio Build Tools 2022:
```bash
vs_buildtools.exe --norestart --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended
```

2. Install Python 3.11.9

## Installation

1. Clone this repository:
```bash
git clone https://github.com/anmaurya001/poc_object_gen.git
cd TRELLIS
```

2. Create and activate a virtual environment in the  directory:
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
```

3. Install dependencies:
```bash
# Update pip and install build tools
python -m pip install --upgrade pip wheel
python -m pip install setuptools==75.8.2

# Install TRELLIS requirements from Windows installation guide
pip install -r requirements-torch.txt
pip install -r requirements-other.txt

# Install POC requirements
pip install -r requirements.txt
```

## Usage
1. Start the LLM NIM
```bash
cd nim_llm
pip install -r requirements.txt
python run_llama.py
```


3. Start the application:
```bash
# On Windows:
set ATTN_BACKEND=flash-attn
set SPCONV_ALGO=native
set XFORMERS_FORCE_DISABLE_TRITON=1
cd TRELLIS/poc_3d_scene
python run.py
```

3. Open your browser to the URL shown in the terminal (typically http://localhost:7860)

4. Use the interface to:
   - Describe your scene
   - Get AI suggestions for objects
   - Generate 3D assets
   - Auto-import into Blender

5. To terminate the application and free VRAM:
```bash
python terminator.py
```
This will:
- Gracefully terminate the Gradio application
- Free up GPU memory
- Allow you to proceed with other operations (e.g., Blender)
  
6. Blender Integration
    - Open Blender
    - Click on Scripting and New.
    - Paste the script from blender/auto_import.py.
    - Click run.
    - Note - If you have new assets, rerun it.

## Acknowledgments

- [TRELLIS](https://github.com/microsoft/TRELLIS) for the 3D generation capabilities
- [Griptape](https://github.com/griptape-ai/griptape) for the agent framework
- [Gradio](https://github.com/gradio-app/gradio) for the web interface
- [TRELLIS Windows Installation Guide](https://github.com/ericcraft-mh/TRELLIS-install-windows) for Windows setup instructions
