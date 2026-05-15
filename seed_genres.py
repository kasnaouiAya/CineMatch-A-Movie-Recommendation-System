import os
import django
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinematch.settings')
django.setup()

from movies.models import Movie, Genre
from django.utils.text import slugify

TMDB_API_KEY = '4a997c6df1132cb092a65e07a38fcd77'

TMDB_GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 14: "Fantasy",
    27: "Horror", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    10751: "Family", 10752: "War", 53: "Thriller", 37: "Western",
}

print("Starting Genre sync from TMDB...")

for movie in Movie.objects.all():
    try:
        resp = requests.get(
            'https://api.themoviedb.org/3/search/movie',
            params={'api_key': TMDB_API_KEY, 'query': movie.title}
        )
        resp.raise_for_status()
        results = resp.json().get('results', [])

        if not results:
            print(f"  ✗ Not found: {movie.title}")
            continue

        genre_ids = results[0].get('genre_ids', [])
        applied_genres = []

        for gid in genre_ids:
            genre_name = TMDB_GENRES.get(gid)
            if genre_name:
                # Handle both unique constraints (slug and name)
                slug = slugify(genre_name)
                genre_obj = Genre.objects.filter(slug=slug).first() \
                         or Genre.objects.filter(name=genre_name).first()
                if not genre_obj:
                    genre_obj = Genre.objects.create(name=genre_name, slug=slug)
                movie.genres.add(genre_obj)
                applied_genres.append(genre_name)

        print(f"  ✓ {movie.title} → {applied_genres}")

        time.sleep(0.25)  # avoid rate limiting

    except Exception as e:
        print(f"  ✗ Error processing '{movie.title}': {e}")

print("\nDone!")