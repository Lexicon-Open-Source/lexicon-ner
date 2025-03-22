# Lexicon Named Entity Recognition for Legal Documents

This project implements Legal Entity Recognition using OpenAI LLM API via LiteLLM with the following features:
- Docker deployment
- Legal entity role recognition (defendant, plaintiff, representative)
- API key authentication
- Environment-based configuration
- Batch processing capability for efficiency
- Support for multilingual text (English and Indonesian)

## Features
- Recognizes and extracts legal entities from text
- Identifies legal roles including defendants, plaintiffs, and representatives
- Handles Indonesian legal terminology
- Provides confidence scores for each recognized entity
- Secures API endpoints with API key authentication
- Uses .env file for easy configuration
- Efficient batch processing for multiple documents
- Special handling for Indonesian names with titles and lineage

## Project Structure
- `app/` - Contains the FastAPI application
- `Dockerfile` - Docker configuration
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Docker Compose configuration
- `.env.sample` - Sample environment variables configuration

## Setup and Usage

### Configuration with .env file

The project uses a `.env` file for configuration. A sample configuration file is provided in `.env.sample`.

To create your own configuration:

```bash
# Copy the sample file to create your own .env file
cp .env.sample .env

# Edit the .env file with your preferred editor
nano .env
```

Important configuration options:
- `API_KEY` - The API key for authentication (default: "lexicon-ner-default-key")
- `REQUIRE_API_KEY` - Whether to require API key authentication (1=enabled, 0=disabled)
- `CACHE_SIZE` - Number of requests to cache (default: 1000)
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)
- `OPENAI_API_KEY` - Your OpenAI API key (required for legal entity recognition)
- `OPENAI_MODEL` - The OpenAI model to use (default: "gpt-4o-mini")

### API Key Security

The API is secured with API key authentication. You can set your API key in the `.env` file or by setting environment variables in your docker-compose.yml file:

```yaml
environment:
  - API_KEY=your-secret-api-key
```

To disable API key security, set the `REQUIRE_API_KEY` environment variable to `0` in the `.env` file.

### OpenAI Integration

The legal entity recognition requires an OpenAI API key. To use this:

1. Get an API key from [OpenAI](https://platform.openai.com/)
2. Add your API key to the `.env` file:
   ```
   OPENAI_API_KEY=your-openai-api-key
   ```
3. Restart the service:
   ```bash
   docker compose down && docker compose up -d
   ```

### Basic Docker Commands

Here are the basic Docker commands to manage the service:

```bash
# Start the service
docker compose up -d

# View logs
docker compose logs -f

# Stop the service
docker compose down

# Rebuild and restart the service (after code changes)
docker compose build
docker compose up -d

# Check if the service is running
docker compose ps
```

### Manual setup

1. Build and run the Docker container:
   ```bash
   # Build the Docker image
   docker compose build

   # Start the service
   docker compose up -d
   ```

2. Access the API at http://localhost:8000

3. API Endpoints:
   - `POST /api/legal-entities` - Identify legal roles in a single text
   - `POST /api/legal-entities/batch` - Identify legal roles in multiple texts (efficient batch processing)
   - `GET /api/health` - Health check endpoint

## API Documentation
Once running, visit http://localhost:8000/docs for the Swagger UI API documentation.

## Example Usage

### Legal Entity Recognition
```bash
# Single text legal entity recognition
curl -X POST "http://localhost:8000/api/legal-entities" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "text": "In the case of Smith v. Jones, the plaintiff John Smith filed a lawsuit against the defendant Sarah Jones."
  }'
```

### Batch Processing
```bash
# Batch processing for multiple texts
curl -X POST "http://localhost:8000/api/legal-entities/batch" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "texts": [
      "In the case of Smith v. Jones, the plaintiff John Smith filed a lawsuit against the defendant Sarah Jones.",
      "Terdakwa BUDI SANTOSO alias BUDI alias SANTO bin WARIMAN telah ditetapkan bersalah.",
      "JAKSA/PENUNTUT UMUM PADA KEJAKSAAN NEGERI TANGERANG melawan Terdakwa H. NAWAWI, S.Ip. bin MUSA"
    ]
  }'
```

## Performance Considerations
The system is optimized for efficiency by:
- Implementing batch processing for multiple documents
- Using proper caching strategies
- Supporting both English and Indonesian legal texts in a single model

Note that the legal entity recognition relies on the OpenAI API, which may have variable latency depending on network conditions and OpenAI's service status.

## Multilingual Support
The system supports both English and Indonesian legal texts. For Indonesian texts, it includes special handling for:
- Academic titles (Drs., Ir., Dr., Prof., etc.)
- Religious titles (H., Hj.)
- Lineage indicators (bin/binti)
- Various alias formats commonly used in Indonesian legal documents
- Indonesian legal terminology (Penggugat, Terdakwa, Jaksa/Penuntut Umum, etc.)