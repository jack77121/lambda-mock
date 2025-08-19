# The python version to use is supplied as an arg from SST
ARG PYTHON_VERSION=3.11

# Build stage with Amazon Linux 2023 for newer GCC
FROM amazonlinux:2023 AS builder

# Install Python 3.11 and build tools
RUN yum update -y && \
    yum install -y python3.11 python3.11-devel python3.11-pip \
                   git gcc gcc-c++ make gfortran \
                   blas-devel lapack-devel openblas-devel \
                   pkgconfig cmake && \
    yum clean all

# Create python symlink for compatibility
RUN ln -sf /usr/bin/python3.11 /usr/bin/python

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Build dependencies
COPY requirements.txt /tmp/requirements.txt
RUN uv pip install -r /tmp/requirements.txt --target /opt/python --system

# Runtime stage
FROM public.ecr.aws/lambda/python:${PYTHON_VERSION}

# Copy built dependencies from builder stage
COPY --from=builder /opt/python ${LAMBDA_TASK_ROOT}

# Perform any steps that you want here:
# Example: pre-bake in model weights from huggingface to image

# Copy the rest of the code
COPY . ${LAMBDA_TASK_ROOT}

# No need to configure the handler or entrypoint - SST will do that