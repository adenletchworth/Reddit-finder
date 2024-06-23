import requests
from bs4 import BeautifulSoup
import json
import numpy as np

def get_page_metadata(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
        except Exception:
            try:
                soup = BeautifulSoup(response.content, 'lxml')
            except Exception:
                try:
                    soup = BeautifulSoup(response.content, 'html5lib')
                except Exception:
                    return '', ''
        title = soup.find('title').text if soup.find('title') else ''
        description = ''
        if soup.find('meta', attrs={'name': 'description'}):
            description = soup.find('meta', attrs={'name': 'description'}).get('content', '')
        elif soup.find('meta', attrs={'property': 'og:description'}):
            description = soup.find('meta', attrs={'property': 'og:description'}).get('content', '')
        return title, description
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError):
        return '', ''

def generate_embeddings(post_json, model, text_weight=0.7):
    try:
        post = json.loads(post_json)
        embeddings = []
        if post.get('title'):
            embeddings.append(text_weight * model.encode(post['title']))
        if post.get('selftext'):
            embeddings.append(text_weight * model.encode(post['selftext']))
        if post.get('url'):
            url_title, url_description = get_page_metadata(post['url'])
            if url_title:
                embeddings.append(text_weight * model.encode(url_title))
            if url_description:
                embeddings.append(text_weight * model.encode(url_description))

        if embeddings:
            return np.mean(embeddings, axis=0).tolist()
        else:
            return [0] * 384
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        print(f"Raw post string: {post_json}")
        return [0] * 384
