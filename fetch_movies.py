import os
import django
import requests
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinematch.settings')
django.setup()

from movies.models import Movie

def fetch_and_save_movies(max_pages=10):
    API_KEY = '4a997c6df1132cb092a65e07a38fcd77'
    BASE_URL = 'https://api.themoviedb.org/3/movie/popular'

    print(f"🚀 Fetching movies from TMDB (up to {max_pages} pages = ~{max_pages * 20} movies)...")

    added   = 0
    updated = 0
    skipped = 0
    failed  = 0

    for page in range(1, max_pages + 1):
        try:
            response = requests.get(
                BASE_URL,
                params={
                    'api_key':       API_KEY,
                    'language':      'en-US',
                    'page':          page,
                    'include_adult': 'false',   # ← tell TMDB to exclude adult content
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            results     = data.get('results', [])
            total_pages = data.get('total_pages', 1)

            print(f"\n📄 Page {page}/{min(max_pages, total_pages)}")

            if not results:
                print("  No results, stopping.")
                break

            for item in results:
                try:
                    # Double-check: skip anything TMDB still marks as adult
                    if item.get('adult', False):
                        print(f"  ⛔ Skipped (adult): {item.get('title')}")
                        skipped += 1
                        continue

                    movie, created = Movie.objects.update_or_create(
                        title=item['title'],
                        defaults={
                            'description':  item.get('overview', ''),
                            'release_year': item.get('release_date', '')[:4] if item.get('release_date') else None,
                            'poster_path':  f"https://image.tmdb.org/t/p/w500{item.get('poster_path', '')}",
                            'tmdb_rating':  item.get('vote_average'),
                            'content_type': 'movie',
                        }
                    )
                    if created:
                        print(f"  ✅ Added:   {movie.title}")
                        added += 1
                    else:
                        print(f"  🔄 Updated: {movie.title}")
                        updated += 1

                except Exception as e:
                    print(f"  ❌ Error saving '{item.get('title')}': {e}")
                    failed += 1

            # Stop if we've reached the last available page
            if page >= total_pages:
                print("\n  ✔ Reached last page of results.")
                break

            time.sleep(0.25)  # be polite to the API

        except Exception as e:
            print(f"❌ Error fetching page {page}: {e}")
            break

    print(f"\n✨ Done! {added} added, {updated} updated, {skipped} skipped (adult), {failed} failed.")
    print("Now run: py seed_tmdb_ratings.py")

if __name__ == "__main__":
    fetch_and_save_movies(max_pages=10)  # change this number to get more movies