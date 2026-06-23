"""
Recipe Ingestion Script for Shikaar LLM
This script reads markdown recipe files, generates embeddings and stores them in Pinecone
"""

import os
from pathlib import Path 
from dotenv import load_dotenv
import openai
from pinecone import Pinecone 
import yaml

# Load environment variables from .env file
load_dotenv()

#Initalize OpaenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

#Initialize Pinecone client
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

#Connect to Pinecone index
index_name = "shikaar-recipes"
index = pc.Index(index_name)

print(f"Connected to Pinecone index: {index_name}")
print(f"Index stats: {index.describe_index_stats()}")

def parse_markdown(file_path):
   """Parse a markdown file and extracts YAML front matter and content
   
   Args:
       file_path (str): Path to the markdown file
    Returns: 
         tuple: (metadata dict, content str)
    """
   with open(file_path, 'r', encoding='utf-8') as f:
       content = f.read()

   #check if file has YAML front matter
   if content.startswith('---'):
       #split on the cloising --- to seperate YAML fron content
       parts = content.split('---', 2)
       yaml_content = parts[1]
       markdown_content = parts[2].strip()
       
       #parse the YAML into a python dictionary
       metadata = yaml.safe_load(yaml_content)
       return metadata, markdown_content
   else:
       # No YAML front matter, return empty metadata
       return {}, content.strip()
   
def generate_embedding(text):
   """Generate embedding for the given text using OpenAI API
   
   Args:
       text (str): Text to generate embedding for

   Returns:
       list: A 1536-dimensional embedding vector
   """
   response = openai.embeddings.create(
        input=text,
        model="text-embedding-3-small"
   )
   embedding = response.data[0].embedding
   return embedding

def ingest_recipes():
    """
    Main function that processes markdown files and uploads to Pinecone
    """
    #Define the path to your recipes folder
    recipes_dir = Path("../knowledge-base/recipes")

    #Get all markdown files (except README.md)
    recipe_files = [f for f in recipes_dir.glob("*.md") if f.name != "README.md"]

    print(f"Found {len(recipe_files)} recipe fils to process")

    #Counter for tracking progress
    processed_count = 0 

    # Loop through each recipe file
    for recipe_file in recipe_files:
        print(f"\nProcessing: {recipe_file.name}")

        # Parse the markdown file
        metadata, content = parse_markdown(recipe_file)

        # Combine metadata and content into one text for embedding
        # This helps the AI understand the full context

        full_text = f"Recipe: {metadata.get('title', 'Untitled')}\n\n"
        full_text += f"Protein: {metadata.get('protein', 'N/A')}\n"
        full_text += f"Species: {metadata.get('species', [])}\n"
        full_text += f"Cuisine: {metadata.get('cuisine', 'N/A')}\n"
        full_text += f"Cooking Method: {metadata.get('cooking_method', 'N/A')}\n"
        full_text += f"Difficulty: {metadata.get('difficulty', 'N/A')}\n\n"
        full_text += content

        print(f" Generating embedding..."  )

        # Generate embedding using OpenAI
        embedding = generate_embedding(full_text)

        print(f" Uploading to Pinecone..."  )

        #Create a unique ID for the recipe
        vector_id = recipe_file.stem

        #Prepare metadata to store with the vector
        vector_metadata = {
            "title": metadata.get("title", "Untitled"),
            "protein": metadata.get("protein", "N/A"),
            "species": metadata.get("species", []),
            "cuisine": metadata.get("cuisine", "N/A"),
            "cooking_method": metadata.get("cooking_method", "N/A"),
            "difficulty": metadata.get("difficulty", "N/A"),
            "content_type": "recipe",
            "source_file": recipe_file.name,
            "text": content[:500]
        }

        # Upload to Pinecone
        index.upsert(vectors=[(vector_id, embedding, vector_metadata)])
        
        processed_count += 1
        print(f"  ✓ Successfully uploaded ({processed_count}/{len(recipe_files)})")

        print(f"\n{'='*50}")
        print(f"Ingestion complete! Processed {processed_count} recipes.")
        print(f"{'='*50}")

# This runs only when you execute this file directly
if __name__ == "__main__":
    print("="*50)
    print("Starting Shikaar LLM Recipe Ingestion")
    print("="*50)
    
    try:
        ingest_recipes()
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("Please check your API keys and file paths.")