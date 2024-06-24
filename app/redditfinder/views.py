from django.http import JsonResponse
from django.shortcuts import render
from .scripts.faiss_index import FaissIndexer
from .scripts.config.mongo import mongo_uri, mongo_db_name, mongo_collection_name_posts, mongo_collection_name_index

faiss_index = FaissIndexer(mongo_uri, mongo_db_name, mongo_collection_name_posts, mongo_collection_name_index)

def index(request):
    return render(request, 'redditfinder/index.html')

def search_text(request):
    query = request.GET.get('query')
    if query:
        distances, indices = faiss_index.search_index(query)
        metadata = faiss_index.fetch_metadata(indices)
        results = {
            "query": query,
            "distances": distances.tolist(),
            "metadata": metadata
        }
        return JsonResponse(results, safe=False)
    return JsonResponse({"error": "No query provided"}, safe=False)

