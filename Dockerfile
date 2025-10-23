FROM python:3.12-slim

WORKDIR /app

# Copy the scripts into the container
COPY merge_duplex.py .
COPY entrypoint.sh .

# Install dependencies
RUN pip install pypdf

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Run the entrypoint script
CMD ["/app/entrypoint.sh"]
