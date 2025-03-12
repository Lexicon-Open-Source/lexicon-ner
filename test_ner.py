#!/usr/bin/env python3
"""
Test script for the Lexicon NER API.
This script sends sample requests to the API to demonstrate its usage.
"""

import json
import requests
import sys
import time

# API endpoint
API_URL = "http://localhost:8000/api/ner"
BATCH_API_URL = "http://localhost:8000/api/ner/batch"

# Sample Indonesian texts
SAMPLE_TEXTS = [
    "Presiden Joko Widodo mengunjungi Jakarta untuk bertemu dengan Menteri Anies Baswedan.",
    "Bank Indonesia memperkirakan pertumbuhan ekonomi tahun 2021 akan mencapai 4,5 persen.",
    "PT Telkom Indonesia telah meluncurkan layanan internet 5G di beberapa kota besar seperti Jakarta, Surabaya, dan Medan.",
    "Gubernur Jawa Barat Ridwan Kamil meresmikan jalan tol Cisumdawu yang menghubungkan Cileunyi dan Sumedang.",
    "Universitas Indonesia mengadakan seminar internasional tentang perkembangan teknologi AI di kawasan ASEAN."
]

def test_single_request():
    """Test a single NER request."""
    print("Testing single text NER...")

    for text in SAMPLE_TEXTS:
        print(f"\nInput: {text}")

        # Send request
        response = requests.post(API_URL, json={"text": text})

        # Check if request was successful
        if response.status_code == 200:
            result = response.json()
            print("Entities found:")
            for entity in result["entities"]:
                print(f"  - {entity['text']} ({entity['type']}) [confidence: {entity['confidence']:.2f}]")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

def test_batch_request():
    """Test a batch NER request."""
    print("\nTesting batch NER...")

    # Send request
    response = requests.post(BATCH_API_URL, json={"texts": SAMPLE_TEXTS})

    # Check if request was successful
    if response.status_code == 200:
        results = response.json()["results"]

        for i, result in enumerate(results):
            print(f"\nInput {i+1}: {result['text']}")
            print("Entities found:")
            for entity in result["entities"]:
                print(f"  - {entity['text']} ({entity['type']}) [confidence: {entity['confidence']:.2f}]")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_performance():
    """Test the performance of the API."""
    print("\nTesting performance...")

    # Warm-up request
    response = requests.post(API_URL, json={"text": SAMPLE_TEXTS[0]})

    # Measure latency for single requests
    start_time = time.time()
    num_requests = 5

    for _ in range(num_requests):
        response = requests.post(API_URL, json={"text": SAMPLE_TEXTS[0]})

    single_latency = (time.time() - start_time) / num_requests
    print(f"Average latency for single requests: {single_latency*1000:.2f} ms")

    # Measure latency for batch request
    start_time = time.time()
    response = requests.post(BATCH_API_URL, json={"texts": SAMPLE_TEXTS})
    batch_latency = time.time() - start_time
    print(f"Latency for batch request with {len(SAMPLE_TEXTS)} texts: {batch_latency*1000:.2f} ms")
    print(f"Average latency per text in batch: {batch_latency*1000/len(SAMPLE_TEXTS):.2f} ms")

if __name__ == "__main__":
    # Check if health endpoint is available
    try:
        health_response = requests.get("http://localhost:8000/api/health")
        if health_response.status_code != 200:
            print("Error: API is not healthy. Please make sure the server is running.")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API. Please make sure the server is running.")
        sys.exit(1)

    # Run tests
    test_single_request()
    test_batch_request()
    test_performance()