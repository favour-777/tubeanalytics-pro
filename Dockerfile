FROM apify/actor-python:3.11

# Copy and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . ./

# Set the entry point
CMD ["python3", "-m", "src.main"]