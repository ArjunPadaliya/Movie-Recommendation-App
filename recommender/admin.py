from django.contrib import admin

# Register your models here.
from recommender.models import Movie, Similarity, Tag, OnlineLink

admin.site.register(Movie)
admin.site.register(Similarity)
admin.site.register(Tag)
admin.site.register(OnlineLink)
