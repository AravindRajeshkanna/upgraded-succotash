FROM nvidia/cuda:13.0.1-devel-ubuntu24.04

ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install tensorflow numpy

COPY matrix_test.py /app/
WORKDIR /app

CMD ["python3", "matrix_test.py"]
