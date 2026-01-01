FROM nvcr.io/nvidia/pytorch:24.06-py3    # Example CUDA+PyTorch base

# Install MPI
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libopenmpi-dev openmpi-bin && \
    rm -rf /var/lib/apt/lists/*

# (Optional) CuPy if you prefer that over raw PyTorch tensors
# RUN pip install cupy-cuda12x

# Add app
WORKDIR /workspace
COPY distributed_gpu_app.py /workspace/distributed_gpu_app.py

# Default command: mpirun launch with 1 GPU per rank
# (Kubernetes container command will override entrypoint)
CMD ["bash", "-c", "sleep infinity"]
