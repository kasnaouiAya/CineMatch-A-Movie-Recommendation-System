import requests
from movies.models import Movie

TMDB_API_KEY = '4a997c6df1132cb092a65e07a38fcd77'

for movie in Movie.objects.all():
    resp = requests.get('https://api.themoviedb.org/3/search/movie', params={'api_key': TMDB_API_KEY, 'query': movie.title})
    results = resp.json().get('results', [])
    if not results:
        print(f"✗ Not found: {movie.title}")
        continue
    tmdb_rating = results[0].get('vote_average', 0)
    movie.tmdb_rating = tmdb_rating
    movie.save(update_fields=['tmdb_rating'])
    print(f"✓ {movie.title} → TMDB: {tmdb_rating}/10")

print("Done!")