import os
import django

# 1. Setup Django environment
# We are using lowercase 'cinematch' to match your ROOT_URLCONF
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinematch.settings')
django.setup()

from movies.models import Movie
from sentence_transformers import SentenceTransformer

def run_force_sync():
    print("--- 🤖 Local AI Sync Starting ---")
    
    # Load Model (Free, local version)
    try:
        print("Loading AI model (all-MiniLM-L6-v2)...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ AI Model Loaded.")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return

    # Get Movies from the database
    all_movies = Movie.objects.all()
    count = all_movies.count()
    
    if count == 0:
        print("❓ No movies found in the database. Check your 'pfa_movie_db' table.")
        return

    print(f"📊 Found {count} movies total. Starting vector generation...")

    for movie in all_movies:
        try:
            if not movie.description:
                print(f"⚠️ Skipping '{movie.title}': No description found.")
                continue
            
            # Generate the 384-dimension vector
            # We use .tolist() because Postgres pgvector needs a Python list
            vector = model.encode(movie.description).tolist()
            
            # Update the specific field
            movie.description_vector = vector
            movie.save(update_fields=['description_vector'])
            
            print(f"✅ Indexed: {movie.title}")
            
        except Exception as e:
            print(f"❌ Failed on '{movie.title}': {e}")

    print("\n--- 🎉 Sync Complete! ---")
    print("You can now go back to your DB and the [NULL] should be replaced with numbers.")

if __name__ == "__main__":
    run_force_sync()