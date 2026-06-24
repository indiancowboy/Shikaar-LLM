"""
Technique Ingestion Script for Shikaar LLM
Reads markdown technique/butchery docs, generates embeddings, stores them in
Pinecone with content_type "technique" so they're retrievable alongside recipes
and cuisines (e.g. "how do I break down a hindquarter").
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import openai
from pinecone import Pinecone
import yaml

# Load environment variables from .env file
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

index_name = "shikaar-recipes"
index = pc.Index(index_name)

print(f"Connected to Pinecone index: {index_name}")
print(f"Index stats: {index.describe_index_stats()}")


def parse_markdown(file_path):
    """Parse a markdown file and extract YAML front matter and content."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if content.startswith("---"):
        parts = content.split("---", 2)
        metadata = yaml.safe_load(parts[1])
        markdown_content = parts[2].strip()
        return metadata, markdown_content
    return {}, content.strip()


def generate_embedding(text):
    """Generate a 1536-dim embedding using OpenAI."""
    response = openai.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding


def ingest_techniques():
    """Process technique markdown files and upload to Pinecone."""
    techniques_dir = Path("../knowledge-base/techniques")
    technique_files = [f for f in techniques_dir.glob("*.md") if f.name != "README.md"]

    print(f"Found {len(technique_files)} technique files to process")

    processed_count = 0
    for technique_file in technique_files:
        print(f"\nProcessing: {technique_file.name}")
        metadata, content = parse_markdown(technique_file)

        full_text = f"Technique: {metadata.get('title', 'Untitled')}\n\n"
        full_text += f"Doc Type: {metadata.get('doc_type', 'technique')}\n"
        full_text += f"Applies To: {metadata.get('applies_to', [])}\n\n"
        full_text += content

        print("  Generating embedding...")
        embedding = generate_embedding(full_text)

        print("  Uploading to Pinecone...")
        vector_id = f"technique_{technique_file.stem}"
        vector_metadata = {
            "title": metadata.get("title", "Untitled"),
            "doc_type": metadata.get("doc_type", "technique"),
            "applies_to": str(metadata.get("applies_to", [])),
            "content_type": "technique",
            "source_file": technique_file.name,
            "text": content[:500],
        }
        index.upsert(vectors=[(vector_id, embedding, vector_metadata)])

        processed_count += 1
        print(f"  ✓ Successfully uploaded ({processed_count}/{len(technique_files)})")

    print(f"\n{'='*50}")
    print(f"Ingestion complete! Processed {processed_count} techniques.")
    print(f"{'='*50}")


if __name__ == "__main__":
    print("=" * 50)
    print("Starting Shikaar LLM Technique Ingestion")
    print("=" * 50)
    try:
        ingest_techniques()
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("Please check your API keys and file paths.")
