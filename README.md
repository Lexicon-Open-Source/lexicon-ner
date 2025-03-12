# Lexicon Named Entity Recognition

This project implements Indonesian Named Entity Recognition using Flair NLP with the following features:
- Docker deployment
- Optimized for low latency
- Named entity type recognition (PER, LOC, ORG)
- Special handling for person titles

## Features
- Recognizes and extracts named entities from Indonesian text
- Removes non-academic titles from person names (e.g., "Presiden", "Gubernur", "Menteri")
- Preserves academic titles (e.g., "Dr.", "Prof.")
- Handles geographic/location identifiers in titles (e.g., "Gubernur Jawa Barat")
- Provides confidence scores for each recognized entity

## Project Structure
- `app/` - Contains the FastAPI application
- `models/` - Directory for storing Flair NLP models
- `Dockerfile` - Docker configuration
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Docker Compose configuration
- `run.sh` - Helper script for managing the service
- `test_ner.py` - Test script for the API

## Setup and Usage

### Using the helper script

The project includes a helper script `run.sh` to simplify common operations:

```bash
# Start the service
./run.sh start

# Check service status
./run.sh status

# View logs
./run.sh logs

# Run tests
./run.sh test

# Rebuild the service (after code changes)
./run.sh rebuild

# Stop the service
./run.sh stop

# Show help
./run.sh help
```

### Manual setup

1. Build and run the Docker container:
   ```
   docker compose up -d
   ```

2. Access the API at http://localhost:8000

3. API Endpoints:
   - `POST /api/ner` - Recognize named entities in a single text
   - `POST /api/ner/batch` - Recognize named entities in multiple texts
   - `GET /api/health` - Health check endpoint

## API Documentation
Once running, visit http://localhost:8000/docs for the Swagger UI API documentation.

## Example Usage
```python
import requests

# Single text NER
response = requests.post(
    "http://localhost:8000/api/ner",
    json={"text": "Presiden Joko Widodo mengunjungi Jakarta untuk bertemu dengan Menteri Anies Baswedan."}
)
print(response.json())

# Batch NER
response = requests.post(
    "http://localhost:8000/api/ner/batch",
    json={
        "texts": [
            "Presiden Joko Widodo mengunjungi Jakarta.",
            "Gubernur Jawa Barat Ridwan Kamil menghadiri rapat di Bandung."
        ]
    }
)
print(response.json())
```

## Performance Considerations
The system is optimized for low latency by:
- Using a lightweight Flair configuration
- Implementing proper caching strategies
- Optimized model loading and inference

## Model Information
The system uses Indonesian NER models from HuggingFace, with fallback options:
1. "ner-multi" - Flair's multilingual NER model
2. "cahya/bert-base-indonesian-NER" - BERT model for Indonesian NER
3. "cahya/xlm-roberta-base-indonesian-NER" - XLM-RoBERTa model for Indonesian NER