# POC 3D Scene Generator

A proof-of-concept application that combines natural language processing with 3D asset generation using TRELLIS.

## Features

- Interactive chat interface for scene planning
- AI-assisted object suggestion and layout
- Automatic 3D asset generation from text prompts
- Blender auto-import functionality for generated assets

## Prerequisites

### Windows Installation (Required for TRELLIS)

Before installing this project, you need to set up the development environment on Windows:

1. Install Visual Studio Build Tools 2022:
```bash
vs_buildtools.exe --norestart --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended
```

2. Install Python 3.11.9

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/poc-3d-scene.git
cd poc-3d-scene
```

2. Create and activate a virtual environment in the POC directory:
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/Mac:
source .venv/bin/activate
```

3. Install dependencies:
```bash
# Update pip and install build tools
python -m pip install --upgrade pip wheel
python -m pip install setuptools==75.8.2

# Install TRELLIS requirements from Windows installation guide
pip install -r https://raw.githubusercontent.com/ericcraft-mh/TRELLIS-install-windows/main/requirements-torch.txt
pip install -r https://raw.githubusercontent.com/ericcraft-mh/TRELLIS-install-windows/main/requirements-other.txt

# Install POC requirements
pip install -r requirements.txt
```

4. Clone TRELLIS in a separate directory (outside this repository):
```bash
# Go to your preferred directory for TRELLIS
cd ..
git clone --recurse-submodules https://github.com/microsoft/TRELLIS.git
```

5. Set up environment variables:
```bash
# On Windows:
set ATTN_BACKEND=flash-attn
set SPCONV_ALGO=native
set XFORMERS_FORCE_DISABLE_TRITON=1

# Set TRELLIS_PATH to point to your TRELLIS installation
# Replace C:/path/to/TRELLIS with your actual TRELLIS path
set TRELLIS_PATH=C:/path/to/TRELLIS

# To make these settings permanent, you can add them to your System Environment Variables
```

Note: The TRELLIS_PATH environment variable must point to your TRELLIS installation directory. This is required for the POC to find and use TRELLIS functionality. You can either:
- Set it temporarily in your terminal session using the command above
- Add it permanently to your System Environment Variables
- Place the TRELLIS repository in one of these locations:
  - Next to the poc-3d-scene directory
  - In your home directory
  - At C:/TRELLIS

## Usage

1. Start the application:
```bash
python run.py
```

2. Open your browser to the URL shown in the terminal (typically http://localhost:7860)

3. Use the interface to:
   - Describe your scene
   - Get AI suggestions for objects
   - Generate 3D assets
   - Auto-import into Blender

## Blender Integration

The `examples/auto_import.py` script can be used in Blender to automatically import generated assets.

## Troubleshooting

If you encounter errors about TRELLIS not being found:
1. Check that your TRELLIS_PATH environment variable is set correctly
2. Verify that the TRELLIS repository exists at the specified path
3. Make sure you've cloned TRELLIS with all its submodules
4. Try using an absolute path for TRELLIS_PATH

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [TRELLIS](https://github.com/microsoft/TRELLIS) for the 3D generation capabilities
- [Griptape](https://github.com/griptape-ai/griptape) for the agent framework
- [Gradio](https://github.com/gradio-app/gradio) for the web interface
- [TRELLIS Windows Installation Guide](https://github.com/ericcraft-mh/TRELLIS-install-windows) for Windows setup instructions