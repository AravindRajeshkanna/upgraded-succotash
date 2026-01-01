FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        openmpi-bin \
        libopenmpi-dev \
        openssh-client openssh-server \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# SSH setup for MPI
RUN useradd -m mpiuser && echo "mpiuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
USER mpiuser
WORKDIR /home/mpiuser

RUN mkdir -p /home/mpiuser/.ssh && \
    ssh-keygen -t rsa -N "" -f /home/mpiuser/.ssh/id_rsa && \
    cat /home/mpiuser/.ssh/id_rsa.pub >> /home/mpiuser/.ssh/authorized_keys && \
    chmod 700 /home/mpiuser/.ssh && \
    chmod 600 /home/mpiuser/.ssh/authorized_keys

# Copy Monte Carlo / HPC code
COPY monte_carlo.c /home/mpiuser/monte_carlo.c
RUN mpicc -O3 -o /home/mpiuser/monte_carlo /home/mpiuser/monte_carlo.c

# Start SSH then sleep, so mpirun can exec into containers
CMD /usr/sbin/sshd -D
