# Lexicon Named Entity Recognition

This project implements Indonesian Named Entity Recognition using Flair NLP with the following features:
- Docker deployment
- Optimized for low latency
- Named entity type recognition (PER, LOC, ORG)
- Special handling for person titles
- API key authentication
- Environment-based configuration
- Legal entity recognition (with ChatGPT API)

## Features
- Recognizes and extracts named entities from Indonesian text
- Removes non-academic titles from person names (e.g., "Presiden", "Gubernur", "Menteri")
- Preserves academic titles (e.g., "Dr.", "Prof.")
- Handles geographic/location identifiers in titles (e.g., "Gubernur Jawa Barat")
- Provides confidence scores for each recognized entity
- Secures API endpoints with API key authentication
- Uses .env file for easy configuration
- Identifies legal roles (defendant, plaintiff, representative) using OpenAI's ChatGPT API

## Project Structure
- `app/` - Contains the FastAPI application
- `models/` - Directory for storing Flair NLP models
- `Dockerfile` - Docker configuration
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Docker Compose configuration
- `run.sh` - Helper script for managing the service
- `test_ner.py` - Test script for NER API
- `test_legal.py` - Test script for legal entity recognition API
- `.env.sample` - Sample environment variables configuration

## Setup and Usage

### Configuration with .env file

The project uses a `.env` file for configuration. A sample configuration file is provided in `.env.sample`.

You can easily edit the configuration using the helper script:
```bash
./run.sh config
```

This will open the `.env` file in your default text editor. If the file doesn't exist, it will be created from the sample.

Important configuration options:
- `API_KEY` - The API key for authentication (default: "lexicon-ner-default-key")
- `REQUIRE_API_KEY` - Whether to require API key authentication (1=enabled, 0=disabled)
- `CACHE_SIZE` - Number of requests to cache (default: 1000)
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)
- `USE_CUDA` - Whether to use GPU for inference (1=enabled, 0=disabled)
- `OPENAI_API_KEY` - Your OpenAI API key (required for legal entity recognition)
- `OPENAI_MODEL` - The OpenAI model to use (default: "gpt-4")

### API Key Security

The API is secured with API key authentication. You can set your API key in the `.env` file or by:

1. Setting the `API_KEY` environment variable before starting the service:
   ```bash
   export API_KEY=your-secret-api-key
   ./run.sh start
   ```

2. Using the `--api-key` option with the run.sh script:
   ```bash
   ./run.sh start --api-key=your-secret-api-key
   ```

To disable API key security, set the `REQUIRE_API_KEY` environment variable to `0` in the `.env` file or use:
```bash
./run.sh start --no-auth
```

### OpenAI Integration

The legal entity recognition feature requires an OpenAI API key. To use this feature:

1. Get an API key from [OpenAI](https://platform.openai.com/)
2. Add your API key to the `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key
   ```
3. Restart the service:
   ```bash
   ./run.sh restart
   ```

### Using the helper script

The project includes a helper script `run.sh` to simplify common operations:

```bash
# Start the service
./run.sh start

# Check service status
./run.sh status

# View logs
./run.sh logs

# Edit configuration
./run.sh config

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
   - `POST /api/legal-entities` - Identify legal roles in a single text
   - `POST /api/legal-entities/batch` - Identify legal roles in multiple texts
   - `GET /api/health` - Health check endpoint

## API Documentation
Once running, visit http://localhost:8000/docs for the Swagger UI API documentation.

## Example Usage

### Named Entity Recognition
```python
import requests
from dotenv import load_dotenv
import os

# Load API key from .env file
load_dotenv()
api_key = os.getenv("API_KEY", "lexicon-ner-default-key")
headers = {"X-API-Key": api_key}

# Single text NER
response = requests.post(
    "http://localhost:8000/api/ner",
    headers=headers,
    json={"text": "Presiden Joko Widodo mengunjungi Jakarta untuk bertemu dengan Menteri Anies Baswedan."}
)
print(response.json())
```

### Legal Entity Recognition
```python
import requests
from dotenv import load_dotenv
import os

# Load API key from .env file
load_dotenv()
api_key = os.getenv("API_KEY", "lexicon-ner-default-key")
headers = {"X-API-Key": api_key}

# Single text legal entity recognition
response = requests.post(
    "http://localhost:8000/api/legal-entities",
    headers=headers,
    json={"text": "In the case of Smith v. Jones, the plaintiff John Smith filed a lawsuit against the defendant Sarah Jones."}
)
print(response.json())
```

## Performance Considerations
The system is optimized for low latency by:
- Using a lightweight Flair configuration
- Implementing proper caching strategies
- Optimized model loading and inference

Note that the legal entity recognition feature relies on the OpenAI API, which may have higher latency than the local NER model.

## Model Information
The system uses different models for different types of entity recognition:

### Named Entity Recognition
1. "ner-multi" - Flair's multilingual NER model
2. "cahya/bert-base-indonesian-NER" - BERT model for Indonesian NER
3. "cahya/xlm-roberta-base-indonesian-NER" - XLM-RoBERTa model for Indonesian NER

### Legal Entity Recognition
- Uses OpenAI's GPT-4 model to analyze legal texts and identify roles
- Requires a valid OpenAI API key