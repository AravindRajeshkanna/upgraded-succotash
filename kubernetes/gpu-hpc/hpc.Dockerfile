FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install OpenMPI + compiler
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        openmpi-bin \
        libopenmpi-dev && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 mpiuser && \
    chown -R mpiuser:mpiuser /home/mpiuser

WORKDIR /home/mpiuser

# Copy and compile as non-root user
COPY --chown=mpiuser:mpiuser monte_carlo.c /home/mpiuser/monte_carlo.c
USER mpiuser

RUN mpicc -O3 -o /home/mpiuser/monte_carlo /home/mpiuser/monte_carlo.c

# Default: mpirun as non-root user
CMD ["mpirun", "-np", "4", "./monte_carlo", "10000000"]
