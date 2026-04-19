from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ProfileForm
from .models import User
from django.db.models import Q

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
    tab = request.GET.get('tab', 'lists')

    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user)

    followers = request.user.followers.all()
    following_ids = set(request.user.following.values_list('id', flat=True))

    return render(request, 'users/profile.html', {
        'form': form,
        'tab': tab,
        'followers': followers,
        'following_ids': following_ids,
        'followers_count': request.user.get_followers_count(),
        'following_count': request.user.get_following_count(),
    })

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