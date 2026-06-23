"""RAG layer — query embedding, Pinecone retrieval, and GPT-4o generation.

This is the keystone the rest of the app reuses: the general "Ask Shikaar"
endpoint, Freezer "Cook First" suggestions, and the meal planner all call
`retrieval.retrieve()` + `generation.generate()`.
"""
