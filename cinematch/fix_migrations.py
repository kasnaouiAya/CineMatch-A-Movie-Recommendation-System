import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinematch.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.db import connection

print("=" * 60)
print("MIGRATIONS IN DATABASE")
print("=" * 60)
with connection.cursor() as cursor:
    cursor.execute("SELECT app, name FROM django_migrations WHERE app = 'users' ORDER BY name;")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

print()
print("=" * 60)
print("MIGRATION FILES IN users/migrations/")
print("=" * 60)
migrations_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users', 'migrations')
for f in sorted(os.listdir(migrations_dir)):
    if f.endswith('.py') and not f.startswith('__'):
        print(f"  {f}")