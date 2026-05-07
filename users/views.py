from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ProfileForm
from django.db.models import Q
from django.http import JsonResponse
from movies.models import MovieList, MovieListItem, Watchlist, Watched, Movie
from django.db import IntegrityError
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
User = get_user_model()  # Toujours utiliser ça avec un custom User
from django.contrib.auth.forms import UserCreationForm

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('genre_test')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if user.is_superuser:
                return redirect('home')
            if not user.genre_test_done:
                return redirect('genre_test')
            return redirect('home')
    else:
        form = LoginForm(request)
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

GENRES = [
    'Action', 'Comedy', 'Drama', 'Horror',
    'Sci-Fi', 'Animation', 'Adventure', 'Mystery',
    'Fantasy', 'Documentary', 'Thriller', 'Romance'
]

@login_required
def genre_test_view(request):
    if request.user.genre_test_done:
        return redirect('home')
    if request.method == 'POST':
        request.user.genre_test_done = True
        request.user.save()
        return redirect('home')
    return render(request, 'users/genre_test.html', {
        'genres': GENRES
    })


@login_required
def profile_view(request):
    user = request.user
    tab = request.GET.get('tab', 'lists')

    if request.method == 'POST' and tab == 'edit':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=user)

    # Get or create default lists
    favorites, _ = MovieList.objects.get_or_create(
        user=user, list_type='favorites',
        defaults={'name': 'Favorites'}
    )
    must_watch, _ = MovieList.objects.get_or_create(
        user=user, list_type='must_watch',
        defaults={'name': 'Must Watch'}
    )

    # COUNTS - requêtes directes
    watchlist_count = Watchlist.objects.filter(user=user).count()
    watched_count = Watched.objects.filter(user=user).count()
    lists_count = MovieList.objects.filter(user=user, list_type='custom').count()

    followers = user.followers.all()
    following_ids = set(user.following.values_list('id', flat=True))

    return render(request, 'users/profile.html', {
        'form': form,
        'tab': tab,
        'user': user,
        'followers': followers,
        'following_ids': following_ids,
        'followers_count': user.get_followers_count(),
        'following_count': user.get_following_count(),
        'lists_count': lists_count,
        'watchlist_count': watchlist_count,
        'watched_count': watched_count,
        'favorites': favorites,
        'must_watch': must_watch,
        'favorites_count': favorites.movie_count,
        'must_watch_count': must_watch.movie_count,
        'custom_lists': MovieList.objects.filter(user=user, list_type='custom'),
    })

@login_required
def create_list(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            MovieList.objects.create(user=request.user, name=name, list_type='custom')
            return JsonResponse({'status': 'ok'})
        return JsonResponse({'status': 'error', 'message': 'Name required'})
    return JsonResponse({'status': 'error', 'message': 'POST required'})

@login_required
def delete_list(request, list_id):
    movie_list = get_object_or_404(MovieList, id=list_id, user=request.user)
    
    # Empêcher la suppression des listes par défaut (Favorites, Must Watch)
    if movie_list.list_type in ['favorites', 'must_watch']:
        messages.error(request, "Cannot delete default lists")
        return redirect('profile')
    
    movie_list.delete()
    messages.success(request, f"'{movie_list.name}' deleted successfully")
    return redirect('profile')

@login_required
def follow_view(request, user_id):
    target = get_object_or_404(User, id=user_id)
    if target != request.user:
        if request.user.following.filter(id=target.id).exists():
            request.user.following.remove(target)
        else:
            request.user.following.add(target)
    return redirect(request.META.get('HTTP_REFERER', 'profile'))

def home_view(request):
    return render(request, 'home.html')

@login_required
def community_view(request):
    query = request.GET.get('q', '').strip()
    tab = request.GET.get('tab', 'followers')
    following_ids = set(request.user.following.values_list('id', flat=True))

    if query:
        users = User.objects.exclude(id=request.user.id).filter(
            Q(username__icontains=query)
        )
    elif tab == 'followers':
        users = request.user.followers.all()
    else:
        users = User.objects.exclude(id=request.user.id).exclude(id__in=following_ids)

    context = {
        'users': users,
        'following_ids': following_ids,
        'tab': tab,
        'query': query,
        'followers_count': request.user.followers.count(),
        'suggestions_count': User.objects.exclude(id=request.user.id).exclude(id__in=following_ids).count(),
    }
    return render(request, 'users/community.html', context)

@login_required
def other_profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    following_ids = set(request.user.following.values_list('id', flat=True))
    tab = request.GET.get('tab', 'lists')

    return render(request, 'users/other_profile.html', {
        'profile_user': profile_user,
        'following_ids': following_ids,
        'is_following': request.user.is_following(profile_user),
        'tab': tab,
        'followers': profile_user.followers.all(),
        'followers_count': profile_user.get_followers_count(),
        'following_count': profile_user.get_following_count(),
    })



@login_required
def notifications_view(request):
    tab = request.GET.get('tab', 'all')
    notifs = request.user.notifications.all()

    if tab == 'follows':
        notifs = notifs.filter(type='follow')
    elif tab == 'likes':
        notifs = notifs.filter(type='like')
    elif tab == 'comments':
        notifs = notifs.filter(type='comment')

    return render(request, 'users/notifications.html', {
        'notifications': notifs,
        'tab': tab,
    })


@login_required
def mark_all_read(request):
    if request.method == 'POST':
        request.user.notifications.update(is_read=True)

    return redirect('notifications')


@login_required
def watchlist_view(request):
    items = Watchlist.objects.filter(user=request.user)\
        .select_related('movie')\
        .order_by('-added_at')

    return render(request, 'users/watchlist.html', {'items': items})


@login_required
def watched_view(request):
    items = Watched.objects.filter(user=request.user)\
        .select_related('movie')\
        .order_by('-watched_at')

    return render(request, 'users/watched.html', {'items': items})


@login_required
def add_to_watch_later(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    Watchlist.objects.get_or_create(
        user=request.user,
        movie=movie
    )

    return redirect(request.META.get('HTTP_REFERER', 'watchlist'))


@login_required
def remove_from_watch_later(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    Watchlist.objects.filter(
        user=request.user,
        movie=movie
    ).delete()

    return redirect(request.META.get('HTTP_REFERER', 'watchlist'))


@login_required
def add_to_watched(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    Watchlist.objects.filter(
        user=request.user,
        movie=movie
    ).delete()

    Watched.objects.get_or_create(
        user=request.user,
        movie=movie
    )

    return redirect(request.META.get('HTTP_REFERER', 'watched'))


@login_required
def remove_from_watched(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    Watched.objects.filter(
        user=request.user,
        movie=movie
    ).delete()

    return redirect(request.META.get('HTTP_REFERER', 'watched'))


@login_required
def list_detail_view(request, list_id):
    movie_list = get_object_or_404(
        MovieList,
        id=list_id,
        user=request.user
    )

    items = MovieListItem.objects.filter(
        movie_list=movie_list
    ).select_related('movie')

    return render(request, 'users/list_detail.html', {
        'movie_list': movie_list,
        'items': items
    })


@staff_member_required
def user_list_view(request):
    users = User.objects.all().order_by('-date_joined')

    return render(request, 'users/user_list.html', {
        'users': users
    })

@staff_member_required
def delete_user(request, user_id):
    if request.method == 'POST':
        user_to_delete = get_object_or_404(User, id=user_id)

        if not user_to_delete.is_superuser:
            user_to_delete.delete()
            messages.success(request, "Utilisateur supprimé avec succès.")
        else:
            messages.error(request, "Impossible de supprimer un administrateur.")

    return redirect('user-list')

@staff_member_required
def edit_user_view(request, user_id):
    user_to_edit = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user_to_edit.username = request.POST.get('username')
        user_to_edit.email = request.POST.get('email')
        user_to_edit.save()

        messages.success(request, "Profil mis à jour.")

        return redirect('user-list')

    return render(request, 'users/edit_user.html', {
        'user_to_edit': user_to_edit
    })




def admin_add_user(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect('user-list')

    else:
        form = RegisterForm()

    return render(request, 'users/admin_add_user.html', {
        'form': form
    })