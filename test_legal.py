#!/usr/bin/env python3
"""
Test script for the Lexicon Legal Entity Recognition API.
This script sends sample requests to the API to demonstrate its usage.
"""

import json
import requests
import sys
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API endpoint
API_URL = "http://localhost:8000/api/legal-entities"
BATCH_API_URL = "http://localhost:8000/api/legal-entities/batch"
HEALTH_URL = "http://localhost:8000/api/health"

# Get API key from environment variable or use default
API_KEY = os.getenv("API_KEY", "lexicon-ner-default-key")
HEADERS = {"X-API-Key": API_KEY}

# Sample legal texts
SAMPLE_TEXTS = [
    "In the case of Smith v. Jones, the plaintiff John Smith filed a lawsuit against the defendant Sarah Jones. Attorney Michael Johnson represents the plaintiff.",
    "Judge Maria Rodriguez presided over the hearing where defendant Thomas Brown was accused of fraud. Prosecutor Jennifer Lee presented evidence against the defendant.",
    "The plaintiff, Company XYZ, represented by attorney David Wilson, alleges that the defendant, John Anderson, breached the contract. The defendant's lawyer, Lisa Campbell, denies these allegations.",
    "Attorney Robert Davis filed a motion on behalf of his client, the defendant James Wilson. The plaintiff, Susan Miller, was not present at the hearing.",
    "In the civil case between Jennifer Harris (plaintiff) and Acme Corporation (defendant), both parties agreed to mediation. The mediator, Dr. Richard Thompson, will oversee the process."
]

def test_single_request():
    """Test a single legal entity recognition request."""
    print("Testing single text legal entity recognition...")

    for text in SAMPLE_TEXTS:
        print(f"\nInput: {text}")

        # Send request
        response = requests.post(API_URL, headers=HEADERS, json={"text": text})

        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            print("Legal entities found:")
            for entity in result["entities"]:
                print(f"  - {entity['name']} ({entity['role']}) [confidence: {entity['confidence']:.2f}]")
        elif response.status_code == 501:
            print("Error: OpenAI API key not configured.")
            print("Please set the OPENAI_API_KEY environment variable.")
            return
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

def test_batch_request():
    """Test a batch legal entity recognition request."""
    print("\nTesting batch legal entity recognition...")

    # Send request
    response = requests.post(BATCH_API_URL, headers=HEADERS, json={"texts": SAMPLE_TEXTS})

    # Check if request was successful
    if response.status_code == 200:
        results = response.json()["results"]

        for i, result in enumerate(results):
            print(f"\nInput {i+1}: {result['text']}")
            print("Legal entities found:")
            for entity in result["entities"]:
                print(f"  - {entity['name']} ({entity['role']}) [confidence: {entity['confidence']:.2f}]")
    elif response.status_code == 501:
        print("Error: OpenAI API key not configured.")
        print("Please set the OPENAI_API_KEY environment variable.")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_performance():
    """Test the performance of the API."""
    print("\nTesting performance...")

    # Check if OpenAI API key is configured
    health_response = requests.get(HEALTH_URL, headers=HEADERS)
    if health_response.status_code == 200:
        health_data = health_response.json()
        if not health_data.get("openai_configured", False):
            print("OpenAI API key not configured. Skipping performance test.")
            return

    # Warm-up request
    response = requests.post(API_URL, headers=HEADERS, json={"text": SAMPLE_TEXTS[0]})
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return

    # Measure latency for a single request (GPT API calls can be slow)
    start_time = time.time()
    response = requests.post(API_URL, headers=HEADERS, json={"text": SAMPLE_TEXTS[0]})
    single_latency = time.time() - start_time
    print(f"Latency for a single request: {single_latency*1000:.2f} ms")

    # Note: We don't test multiple requests for performance due to potential API rate limits and cost

if __name__ == "__main__":
    # Check if health endpoint is available
    try:
        health_response = requests.get(HEALTH_URL, headers=HEADERS)
        if health_response.status_code != 200:
            print("Error: API is not healthy. Please make sure the server is running.")
            sys.exit(1)

        # Check if OpenAI API is configured
        health_data = health_response.json()
        if not health_data.get("openai_configured", False):
            print("Warning: OpenAI API key not configured. Legal entity recognition will not work.")
            print("Please set the OPENAI_API_KEY environment variable.")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Please make sure the server is running.")
        sys.exit(1)

    # Run tests
    test_single_request()
    test_batch_request()
    test_performance()