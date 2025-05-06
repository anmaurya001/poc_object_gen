# Use an official NVIDIA CUDA development image as the base
FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04

# Set environment variable for GPU architecture compatibility during compilation
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.7;8.9"

# Install core system packages needed for building and running (as root)
RUN apt update && apt-get install -yq --no-install-recommends \
    python3 \
    python3-dev \
    git \
    curl \
    ninja-build \
    libgl1 \
    libglib2.0-0 \
    libxrender1 \
    libsm6 \
    libxext6 \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Install pip using the recommended get-pip.py method (as root)
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \
    && python3 get-pip.py \
    && rm get-pip.py

# Install essential Python packages including the pydantic fix and wheel (as root)
RUN pip install \
    pydantic==2.10.6 \
    wheel

# Create symlink from python3 to python so commands expecting 'python' work (as root)
RUN ln -s /usr/bin/python3 /usr/bin/python

# --- Clone and Setup Application Code ---
# Create the application directory and clone the repository into it (as root)
RUN mkdir -p /app/trellis && \
    git clone --recurse-submodules https://github.com/microsoft/TRELLIS.git /app/trellis

# Create the specific cache directory location (as root)
# This will be the target for the volume mount
RUN mkdir -p /app/persistent_cache

# Set the working directory to the cloned repository for subsequent commands
WORKDIR /app/trellis

# Install core PyTorch and torchvision for CUDA 12.1 (as root)
RUN pip install \
    torch==2.4.0 \
    torchvision==0.19 --index-url https://download.pytorch.org/whl/cu121

# Install basic TRELLIS dependencies (as root)
RUN pip install \
    pillow imageio imageio-ffmpeg tqdm easydict \
    opencv-python-headless scipy ninja \
    onnxruntime trimesh xatlas \
    pyvista pymeshfix \
    igraph \
    transformers \
    plyfile

# Install utils3d from git (as root)
RUN pip install git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8

# Install XFORMERS (as root)
RUN pip install xformers==0.0.27.post2 --index-url https://download.pytorch.org/whl/cu121

# Install FLASHATTN (as root)
RUN pip install flash-attn

# Install KAOLIN (as root)
RUN pip install kaolin -f https://nvidia-kaolin.s3.us-east-2.amazonaws.com/torch-2.4.0_cu121.html

# Install SPCONV (as root)
RUN pip install spconv-cu120

# Install Open3D (as root)
RUN pip install open3d

# Install TRELLIS components from source (as root)
RUN mkdir -p /tmp/extensions && \
    git clone https://github.com/NVlabs/nvdiffrast.git /tmp/extensions/nvdiffrast && \
    pip install /tmp/extensions/nvdiffrast && \
    git clone --recurse-submodules https://github.com/JeffreyXiang/diffoctreerast.git /tmp/extensions/diffoctreerast && \
    pip install /tmp/extensions/diffoctreerast && \
    git clone https://github.com/autonomousvision/mip-splatting.git /tmp/extensions/mip-splatting && \
    pip install /tmp/extensions/mip-splatting/submodules/diff-gaussian-rasterization/ && \
    rm -rf /tmp/extensions

# Install vox2seq from the cloned repository (as root)
RUN pip install extensions/vox2seq

# Install DEMO dependencies (as root)
RUN pip install gradio==4.44.1 gradio_litmodel3d==0.0.1

# Install DISO (as root)
#RUN pip install diso

# Install rembg (as root)
RUN pip install rembg

# Clean up temporary source directories
RUN rm -rf /tmp/extensions # If /tmp/extensions was used for cloning sources

# --- Entrypoint Setup ---
# Copy the entrypoint script into the container and make it executable (as root)
# Ownership will be root:root by default
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# --- Runtime Configuration ---
EXPOSE 7860

# Set environment variables for Gradio
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"

# Set the entrypoint script to run first
ENTRYPOINT ["/entrypoint.sh"]

# Set the default command
CMD ["python", "app.py"]