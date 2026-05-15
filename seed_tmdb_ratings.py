import os
import django
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinematch.settings')
django.setup()

from movies.models import Movie

TMDB_API_KEY = '4a997c6df1132cb092a65e07a38fcd77'

print("Starting TMDB rating sync...")

updated = 0
skipped = 0
failed  = 0

for movie in Movie.objects.all():
    try:
        # ------------------------------------------------------------------
        # 1. Prefer searching by TMDB ID if your model stores it
        #    (most accurate — avoids wrong-movie matches)
        # ------------------------------------------------------------------
        if hasattr(movie, 'tmdb_id') and movie.tmdb_id:
            resp = requests.get(
                f'https://api.themoviedb.org/3/movie/{movie.tmdb_id}',
                params={'api_key': TMDB_API_KEY},
            )
        else:
            # Fallback: search by title + year to reduce wrong matches
            params = {'api_key': TMDB_API_KEY, 'query': movie.title}
            if hasattr(movie, 'release_year') and movie.release_year:
                params['year'] = movie.release_year
            resp = requests.get(
                'https://api.themoviedb.org/3/search/movie',
                params=params,
            )

        resp.raise_for_status()
        data = resp.json()

        # ------------------------------------------------------------------
        # 2. Extract rating
        # ------------------------------------------------------------------
        if hasattr(movie, 'tmdb_id') and movie.tmdb_id:
            # Direct movie endpoint returns the object directly
            tmdb_rating = data.get('vote_average')
        else:
            results = data.get('results', [])
            if not results:
                print(f"  ✗ Not found: {movie.title}")
                skipped += 1
                continue
            tmdb_rating = results[0].get('vote_average')

        if tmdb_rating is None:
            print(f"  ✗ No rating returned for: {movie.title}")
            skipped += 1
            continue

        # ------------------------------------------------------------------
        # 3. Save to tmdb_rating (the actual model field)
        #    The templates need to display tmdb_rating, not average_rating
        # ------------------------------------------------------------------
        movie.tmdb_rating = tmdb_rating
        movie.save(update_fields=['tmdb_rating'])

        print(f"  ✓ {movie.title} → {tmdb_rating}/10")
        updated += 1

        # Be kind to the API — avoid rate limiting
        time.sleep(0.25)

    except Exception as e:
        print(f"  ✗ Error on '{movie.title}': {e}")
        failed += 1

print(f"\nDone — {updated} updated, {skipped} skipped, {failed} failed")