# Use an official NVIDIA CUDA development image as the base
FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04

# Set environment variable for GPU architecture compatibility during compilation
ENV TORCH_CUDA_ARCH_LIST="8.0;8.6;8.7;8.9"

# Install core system packages needed for building and running (as root)
RUN apt update && apt-get install -yq --no-install-recommends \
    python3 python3-dev git curl ninja-build \
    libgl1 libglib2.0-0 libxrender1 libsm6 libxext6 \
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

# --- Removed custom cache directory creation ---
# The cache will be managed by the volume mount to /home/user/.cache

# Set the working directory to the cloned repository for subsequent commands
WORKDIR /app/trellis

# Install core PyTorch... (same as before)
RUN pip install \
    torch==2.4.0 \
    torchvision==0.19 --index-url https://download.pytorch.org/whl/cu121

# Install basic TRELLIS dependencies... (same as before, including rembg)
RUN pip install \
    pillow imageio imageio-ffmpeg tqdm easydict \
    opencv-python-headless scipy ninja \
    onnxruntime trimesh xatlas \
    pyvista pymeshfix \
    igraph \
    transformers \
    plyfile \
    rembg

# Install utils3d... (same as before)
RUN pip install git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8

# Install XFORMERS... (same as before)
RUN pip install xformers==0.0.27.post2 --index-url https://download.pytorch.org/whl/cu121

# Install FLASHATTN... (same as before)
RUN pip install flash-attn

# Install KAOLIN... (same as before)
RUN pip install kaolin -f https://nvidia-kaolin.s3.us-east-2.amazonaws.com/torch-2.4.0_cu121.html

# Install SPCONV... (same as before)
RUN pip install spconv-cu120

# Install Open3D... (same as before)
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

# Install vox2seq... (same as before)
RUN pip install extensions/vox2seq

# Install DEMO dependencies (as root)
RUN pip install gradio==4.44.1 gradio_litmodel3d==0.0.1

# Clean up temporary source directories
RUN rm -rf /tmp/extensions

# --- User Setup (Recommended for Production) ---
# Create a non-root user to run the application
RUN useradd -ms /bin/bash user
# Create the user's standard home directory and standard cache directory (as root)
RUN mkdir -p /home/user/.cache
# Change ownership of the cloned code and the user's home/cache directories to the non-root user
RUN chown -R user:user /app/trellis /home/user

# Switch to the non-root user for subsequent commands and runtime
USER user

# Ensure standard binary directories are in the PATH for the non-root user
ENV PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

# Ensure the working directory is correct for the non-root user at runtime
WORKDIR /app/trellis

# --- Entrypoint Setup ---
# Copy the entrypoint script into the container and make it executable
# Ensure ownership is correct for the 'user'
COPY --chown=user:user entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# --- Runtime Configuration ---
EXPOSE 7860

# Set environment variables for Gradio
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"

# Set the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# Set the default command
CMD ["python", "app.py"]