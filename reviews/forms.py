from django import forms
from .models import Rating, Review

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score']

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['body']  
        widgets = {
            'body': forms.Textarea(attrs={
                'placeholder': 'Write your review here...',
                'rows': 4,
            })
        }
        labels = {
            'body': 'Your Review'
        }