"""
Cuisine Ingestion Script for Shikaar LLM
This script reads markdown cuisine profile files, generates embeddings and stores them in Pinecone
"""

import os
from pathlib import Path 
from dotenv import load_dotenv
import openai
from pinecone import Pinecone 
import yaml

# Load environment variables from. env file
load_dotenv()

#Initialize OpenAI and Pinecone client
openai.api_key = os.getenv("OPENAI_API_KEY")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
              
#Connect to the Pinecone index
index_name = "shikaar-recipes"
index = pc.Index(index_name)

print(f"Connected to Pinecone index: {index_name}")
print(f"Index stats: {index.describe_index_stats()}")

def parse_markdown(file_path):
    """
    Parse a markdown file and extract YAML front matter and content
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        tuple: (metadata dict, content string)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if file has YAML front matter (starts with ---)
    if content.startswith('---'):
        # Split on the closing --- to separate YAML from content
        parts = content.split('---', 2)
        yaml_content = parts[1]
        markdown_content = parts[2].strip()
        
        # Parse the YAML into a Python dictionary
        metadata = yaml.safe_load(yaml_content)
        
        return metadata, markdown_content
    else:
        # No YAML front matter, return empty metadata
        return {}, content.strip()


def generate_embedding(text):
    """
    Generates an embedding vector for the given text using OpenAI
    
    Args:
        text: The text to embed
        
    Returns:
        list: A 1536-dimensional embedding vector
    """
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    
    # Extract the embedding vector from the response
    embedding = response.data[0].embedding
    
    return embedding

def ingest_cuisines():
    """
    Main function that processes cuisine profile markdown files and uploads to Pinecone
    """
    # Define the path to your cuisines folder
    cuisines_dir = Path("../knowledge-base/cuisines")
    
    # Get all markdown files (except README)
    cuisine_files = [f for f in cuisines_dir.glob("*.md") if f.name != "README.md"]
    
    print(f"Found {len(cuisine_files)} cuisine files to process")
    
    # Counter for tracking progress
    processed_count = 0
    
    # Loop through each cuisine file
    for cuisine_file in cuisine_files:
        print(f"\nProcessing: {cuisine_file.name}")
        
        # Parse the markdown file
        metadata, content = parse_markdown(cuisine_file)
        
        # Combine metadata and content into one text for embedding
        # Cuisines have different fields than recipes
        full_text = f"Cuisine: {metadata.get('title', 'Untitled')}\n\n"
        full_text += f"Region Type: {metadata.get('region_type', 'N/A')}\n"
        full_text += f"Flavor Profile: {metadata.get('flavor_profile', [])}\n"
        full_text += f"Heat Level: {metadata.get('heat_level_default', 'N/A')}\n"
        full_text += f"Doc Type: {metadata.get('doc_type', 'N/A')}\n\n"
        full_text += content
        
        print(f"  Generating embedding...")

        # Generate the embedding
        embedding = generate_embedding(full_text)
        
        print(f"  Uploading to Pinecone...")
        
        # Create a unique ID for this cuisine (using filename without .md)
        vector_id = f"cuisine_{cuisine_file.stem}"
        
        # Prepare metadata to store with the vector
        vector_metadata = {
            "title": metadata.get('title', 'Untitled'),
            "region_type": metadata.get('region_type', 'N/A'),
            "flavor_profile": str(metadata.get('flavor_profile', [])),  # Convert list to string
            "heat_level_default": metadata.get('heat_level_default', 'N/A'),
            "doc_type": metadata.get('doc_type', 'cuisine_profile'),
            "content_type": "cuisine",  # Important: identifies this as a cuisine
            "source_file": cuisine_file.name,
            "text": content[:500]  # Store first 500 chars for preview
        }
        
        # Upload to Pinecone
        index.upsert(vectors=[(vector_id, embedding, vector_metadata)])
        
        processed_count += 1
        print(f"  ✓ Successfully uploaded ({processed_count}/{len(cuisine_files)})")
    
    print(f"\n{'='*50}")
    print(f"Ingestion complete! Processed {processed_count} cuisines.")
    print(f"{'='*50}")

    # This runs only when you execute this file directly
if __name__ == "__main__":
    print("="*50)
    print("Starting Shikaar LLM Cuisine Ingestion")
    print("="*50)
    
    try:
        ingest_cuisines()
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("Please check your API keys and file paths.")
