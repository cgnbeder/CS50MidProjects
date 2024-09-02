from django.contrib.auth.models import AbstractUser
from django.db import models
from .utils import generate_unique_slug
from django.utils.text import slugify


class User(AbstractUser):
    pass


class Category(models.Model):
    Category = models.CharField(max_length=20)
    created_date = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return str(self.Category)

    def save(self, *args, **kwargs):
        self.Category = self.Category.upper()
        return super(Category, self).save(*args, **kwargs)

class Listing(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="creator")
    list_title = models.CharField(max_length=120, verbose_name="Give a title")
    image_url = models.URLField(verbose_name="Image url", blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category')
    slug = models.SlugField(max_length=264, unique=True, blank=True)
    description = models.TextField(verbose_name='Description', blank=True)
    base_price = models.FloatField();
    current_price = models.FloatField(null=True, blank=True)
    active = models.BooleanField(default=True)
    winner = models.CharField(max_length=120, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.list_title

    def save(self, *args, **kwargs):
        self.category = self.category.upper()
        return super(Listing, self).save(*args, **kwargs)

    class Meta:
        ordering= ['-created_date',]


    def save(self, *args, **kwargs):
        if self.slug:  # edit
            if slugify(self.list_title) != self.slug:
                self.slug = generate_unique_slug(Listing, self.list_title)
        else:  # create
            self.slug = generate_unique_slug(Listing, self.list_title)
        super(Listing, self).save(*args, **kwargs)




class Comment(models.Model):
    item = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='listing_comment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_comment')
    comment = models.TextField()
    comment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"'{self.comment}'- by {self.user} for -{self.item}"

    class Meta:
        ordering = ['-comment_date']


class WatchList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watch_user')
    item = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='watch_item')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item.list_title + ' by ' + self.user.username

    class Meta:
        ordering = ['-created']

class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Bid_user")
    item = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name="Bid_item")
    bid_price = models.FloatField();
    bid_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item.list_title + ' by ' + self.user.username

    class Meta:
        ordering = ['-bid_price']
