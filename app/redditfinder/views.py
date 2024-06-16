from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to Reddit Finder!")

def about(request):
    return HttpResponse("About Reddit Finder")

def addSubreddit(request):
    return HttpResponse("Add a subreddit")

def searchSubreddit(request):
    return HttpResponse("Search a subreddit")

def searchReddit(request):
    return HttpResponse("Search Reddit")


