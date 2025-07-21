# Dockerfile
# Use a specific AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.9

# Install system dependencies required by pdfplumber (Poppler utils)
RUN yum update -y && \
    yum install -y poppler-utils && \
    yum clean all

# Set the working directory in the container
WORKDIR /var/task

# Copy requirements.txt and install Python dependencies
# This step should be before copying other application code to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
# The .dockerignore file will prevent 'utils/local_file_utils.py' and 'local_output/' from being copied
COPY . .

# Set the CMD to your Lambda handler (main.lambda_handler)
CMD [ "main.lambda_handler" ]
