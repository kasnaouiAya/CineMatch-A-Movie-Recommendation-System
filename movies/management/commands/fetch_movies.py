import requests
from django.core.management.base import BaseCommand
from movies.models import Movie

class Command(BaseCommand):
    help = 'Fetch movies including posters from TMDB and save to database'

    def handle(self, *args, **kwargs):
        api_key = '4a997c6df1132cb092a65e07a38fcd77'
        
        # Fetching first 5 pages (100 movies)
        for page_num in range(1, 6):
            self.stdout.write(f"--- Fetching Page {page_num} ---")
            
            url = f"https://api.themoviedb.org/3/discover/movie?api_key={api_key}&language=en-US&sort_by=popularity.desc&include_adult=false&page={page_num}"

            try:
                response = requests.get(url)
                
                if response.status_code == 200:
                    movies_data = response.json().get('results', [])
                    
                    for item in movies_data:
                        # get_or_create checks by title. 
                        # We use 'defaults' to update/set the other fields.
                        movie, created = Movie.objects.get_or_create(
                            title=item['title'],
                            defaults={
                                'description': item.get('overview', 'No description available.'),
                                'poster_path': f"https://image.tmdb.org/t/p/w500{item.get('poster_path', '')}" if item.get('poster_path') else '',
}
                        )
                        
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Added: {movie.title}"))
                        else:
                            # Update the poster_path even if the movie already exists
                            movie.poster_path = f"https://image.tmdb.org/t/p/w500{item.get('poster_path', '')}" if item.get('poster_path') else ''
                            movie.save()
                            self.stdout.write(f"Updated/Skipped: {movie.title}")
                            
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to fetch Page {page_num}. Status: {response.status_code}"))

            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Connection error: {e}"))

        self.stdout.write(self.style.SUCCESS("\nDone! Database is updated with posters."))