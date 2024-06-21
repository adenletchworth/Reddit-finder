import matplotlib.pyplot as plt
from pymongo import MongoClient

mongo_url = 'mongodb://host.docker.internal:27017/'

client = MongoClient(mongo_url)
db = client['Reddit']
collection = db['posts']

posts = list(collection.find())

posts_with_selftext = [post for post in posts if post['selftext']]
posts_without_selftext = [post for post in posts if not post['selftext']]

def count_attributes(posts):
    url_count = sum(1 for post in posts if post.get('url'))
    media_count = sum(1 for post in posts if post.get('media'))
    both_count = sum(1 for post in posts if post.get('url') and post.get('media'))
    return url_count, media_count, both_count

url_with_selftext, media_with_selftext, both_with_selftext = count_attributes(posts_with_selftext)
url_without_selftext, media_without_selftext, both_without_selftext = count_attributes(posts_without_selftext)

labels = ['URL', 'Media', 'Both']
counts_with_selftext = [url_with_selftext, media_with_selftext, both_with_selftext]
counts_without_selftext = [url_without_selftext, media_without_selftext, both_without_selftext]

fig, ax = plt.subplots(1, 2, figsize=(14, 6))

ax[0].bar(labels, counts_with_selftext, color=['blue', 'green', 'purple'])
ax[0].set_title('Posts with Selftext')
ax[0].set_xlabel('Attributes')
ax[0].set_ylabel('Count')

ax[1].bar(labels, counts_without_selftext, color=['blue', 'green', 'purple'])
ax[1].set_title('Posts without Selftext')
ax[1].set_xlabel('Attributes')
ax[1].set_ylabel('Count')

plt.tight_layout()
plt.show()
plt.savefig('./index/images/posts_visualization.png')