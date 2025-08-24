# The python version to use is supplied as an arg from SST
ARG PYTHON_VERSION=3.11

# Use an official AWS Lambda base image for Python
FROM public.ecr.aws/lambda/python:${PYTHON_VERSION}

# Install build tools for numpy compilation
RUN yum update -y && \
    yum install -y git gcc gcc-c++ make gfortran \
                   blas-devel lapack-devel python3-devel && \
    yum clean all

# Install UV to manage your python runtime
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install the dependencies to the lambda runtime
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN uv pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt --target ${LAMBDA_TASK_ROOT} --system
# RUN uv pip install -r ${LAMBDA_TASK_ROOT}/requirements.txt --target ${LAMBDA_TASK_ROOT} --system --only-binary=:all:

# Copy pyproject.toml first for dependency installation
# COPY pyproject.toml ${LAMBDA_TASK_ROOT}/

# Install dependencies using pyproject.toml
# RUN cd ${LAMBDA_TASK_ROOT} && uv sync --frozen --no-dev

# Copy the rest of the source code
COPY . ${LAMBDA_TASK_ROOT}/
# COPY ./src/v1_lambda_ess_irr_evaluation/shared/core/tou_data_simple_2025.csv ${LAMBDA_TASK_ROOT}/v1_lambda_ess_irr_evaluation/shared/core/tou_data_simple_2025.csv
# COPY ./src/v1_lambda_ess_irr_evaluation/shared/core/ami_data.db ${LAMBDA_TASK_ROOT}/v1_lambda_ess_irr_evaluation/shared/core/ami_data.db

# Clean up any numpy source directories that might cause conflicts
RUN find ${LAMBDA_TASK_ROOT} -name "numpy-*" -type d -exec rm -rf {} + 2>/dev/null || true
RUN find ${LAMBDA_TASK_ROOT} -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# No need to configure the handler or entrypoint - SST will do that