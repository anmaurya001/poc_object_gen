#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Ensure we are in the application directory
cd /app/trellis

echo "Starting TRELLIS container entrypoint (running as user)..."

# Removed custom cache directory setup and HF_HOME/TORCH_HOME exports.
# Hugging Face and PyTorch will use their default cache locations
# within ~/.cache/, which is handled by the volume mount to /home/user/.cache in podman run.

echo "Checking for and downloading TRELLIS model (requires GPU access)..."
# Use the absolute path to the python executable
/usr/bin/python -u -c "from trellis.pipelines import TrellisImageTo3DPipeline; TrellisImageTo3DPipeline.from_pretrained('JeffreyXiang/TRELLIS-image-large')"
echo "Model download/check complete."

# --- Potential Runtime Fixes/Installations ---
# If 'diso' or 'rembg' still fail build and were needed at runtime,
# you could potentially add a check and install here.
# Use the absolute path for pip via python -m pip
# if ! /usr/bin/python -c "import diso" &> /dev/null; then
#   echo "Installing diso at runtime..."
#   /usr/bin/python -m pip install diso
# fi
# if ! /usr/bin/python -c "import rembg" &> /dev/null; then
#   echo "Installing rembg at runtime..."
#   /usr/bin/python -m pip install rembg
# fi
# --- End Runtime Fixes ---


echo "Executing main application command..."
exec "$@"