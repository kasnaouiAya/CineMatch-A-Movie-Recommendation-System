import requests
from movies.models import Movie, Genre

TMDB_API_KEY = '4a997c6df1132cb092a65e07a38fcd77'

TMDB_GENRES = {
    28: "Action", 12: "Adventure", 16: "Animation", 35: "Comedy",
    80: "Crime", 99: "Documentary", 18: "Drama", 14: "Fantasy",
    27: "Horror", 9648: "Mystery", 10749: "Romance", 878: "Sci-Fi",
    53: "Thriller", 37: "Western",
}

for movie in Movie.objects.all():
    resp = requests.get('https://api.themoviedb.org/3/search/movie', params={'api_key': TMDB_API_KEY, 'query': movie.title})
    results = resp.json().get('results', [])
    if not results:
        print(f"✗ Not found: {movie.title}")
        continue
    genre_ids = results[0].get('genre_ids', [])
    for gid in genre_ids:
        genre_name = TMDB_GENRES.get(gid)
        if genre_name:
            genre_obj = Genre.objects.filter(name=genre_name).first()
            if genre_obj:
                movie.genres.add(genre_obj)
    print(f"✓ {movie.title} → {[TMDB_GENRES.get(g) for g in genre_ids]}")

print("Done!")