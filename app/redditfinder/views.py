from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .scripts.faiss_index import FaissSearcher
from .scripts.config.mongo import mongo_uri, mongo_db_name, mongo_collection_name_index

faiss_index = FaissSearcher(mongo_uri, mongo_db_name, mongo_collection_name_index)

def index(request):
    return render(request, 'redditfinder/index.html')

def search_text(request):
    query = request.GET.get('query')
    if query:
        distances, indices = faiss_index.search(query, k=6, query_type='text')
        metadata = faiss_index.fetch_metadata(indices)
        results = {
            "query": query,
            "distances": distances.tolist(),
            "metadata": metadata
        }
        return JsonResponse(results, safe=False)
    return JsonResponse({"error": "No query provided"}, safe=False)

@csrf_exempt
def search_image(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            distances, indices = faiss_index.search(image, k=6, query_type='image')
            metadata = faiss_index.fetch_metadata(indices)
            results = {
                "distances": distances.tolist(),
                "metadata": metadata
            }
            return JsonResponse(results, safe=False)
    return JsonResponse({"error": "No image provided"}, safe=False)
