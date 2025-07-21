    # Dockerfile
    # Use a specific AWS Lambda Python base image
    # This image is based on Amazon Linux, which is optimized for Lambda.
    FROM public.ecr.aws/lambda/python:3.9

    # Install system dependencies required by pdfplumber (Poppler utils)
    # 'yum' is the package manager for Amazon Linux.
    RUN yum update -y && \
        yum install -y poppler-utils && \
        yum clean all

    # Set the working directory in the container
    WORKDIR /var/task

    # Copy your application code into the container
    # The order matters for Docker caching: copy requirements.txt first
    # so pip install is only re-run if requirements.txt changes.
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    # Copy the rest of your application code
    COPY main.py .
    COPY config/ config/
    COPY utils/ utils/
    COPY UNSC/ UNSC/
    COPY KDN/ KDN/

    # Set the CMD to your Lambda handler (main.lambda_handler)
    # This tells Lambda which function to call when your function is invoked.
    CMD [ "main.lambda_handler" ]
    