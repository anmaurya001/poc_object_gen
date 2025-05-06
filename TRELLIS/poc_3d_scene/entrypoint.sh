#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status.

# Ensure we are in the application directory (redundant if WORKDIR is set correctly, but safe)
cd /app/trellis

echo "Starting TRELLIS container entrypoint (running as root)..."

# Set cache directories for Hugging Face and PyTorch to subdirectories
# within the persistent volume mount point /app/persistent_cache
export HF_HOME="/app/persistent_cache/huggingface"
export TORCH_HOME="/app/persistent_cache/torch"

# Ensure these cache subdirectories exist within the mounted volume (important!)
# This handles the case where the volume is newly created or empty
mkdir -p "$HF_HOME" "$TORCH_HOME"

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