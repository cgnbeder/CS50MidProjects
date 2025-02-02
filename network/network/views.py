from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect,Http404
import json
from django.shortcuts import render,redirect
from django.urls import reverse
from . import forms
from .models import *
from django.db.models import F
from . import util
import time
from django.utils import timezone
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger

def index(request,message =""):
    if request.user.is_authenticated:
        all_posts = Post.objects.all().order_by('-date_and_time')
        allposts = paginate(request,all_posts)
        post_liked_ids = get_myliked_post(request).values_list("id",flat=True)
        return render(request,"network/index.html",{
            "allposts":allposts,
            "post_liked_ids":post_liked_ids,
            "message":message,
            "index": "active",
        })
    else:
        return HttpResponseRedirect(reverse("network:login"))

def paginate(request,argument):
    page_number = request.GET.get('page',1)
    paginator = Paginator(argument, 10)

    try:
        paginated_argument = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_argument = paginator.page(1)
    except EmptyPage:
        paginated_argument = paginator.page(paginator.num_pages)

    return paginated_argument



def login_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("network:index"))
    else:
        if request.method == "POST":

            # Attempt to sign user in
            username = request.POST["username"]
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)

            # Check if authentication successful
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse("network:index"))
            else:
                return render(request, "network/login.html", {
                    "message": "Invalid username and/or password."
                })
        else:
            return render(request, "network/login.html", context={"login":"active"})


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("network:index"))


def register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("network:index"))
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:

            user = User.objects.create_user(username, email, password)
            user.save()

        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("network:index"))
    else:
        return render(request, "network/register.html", context={"register":"active"})

def newpost(request):
    if request.user.is_authenticated:
        if request.method == "GET":

            newpost_form= forms.NewPostForm()
            return render(request, "network/newpost.html",{
                "newpost_form":newpost_form

            })
        else:
            # get contents from form
            newpost_form = forms.NewPostForm(request.POST)
            username = request.user.username

            if newpost_form.is_valid():

                content = newpost_form.cleaned_data["contents"]

                if len(content)>0:
                    # update POST model
                    username = User.objects.get(username = username)
                    date_time = timezone.now()

                    post = Post(contents = content,user_id=username,date_and_time=date_time,num_of_likes=0)
                    post.save()
                    return HttpResponseRedirect(reverse("network:index"))

                else:
                    return render (request,"network/newpost.html",{
                        "newpost_form":newpost_form,
                    })
            else:
                return render (request,"network/newpost.html",{
                        "newpost_form":newpost_form,
                })
    else:
        return HttpResponseRedirect(reverse("network:login"))

def profile(request,user="",category=""):

    if request.user.is_authenticated:
        if request.method == "GET":
            update_follow_form= forms.updatefollowForm(request.GET)
        else:
            update_follow_form= forms.updatefollowForm(request.POST)

        if len(user) == 0 or request.user.username == user:
            # profile page for current user

            return render(request,'network/profile.html',
                {
                "page_info":"current user",
                "username":request.user.username,
                "update_follow_form":update_follow_form,
                "category":category,
                "profile": "text-white",
                })
        else:
            # profile page for other user
            if User.objects.filter(username = user):
                # get user object
                userobj = util.get_user_obj_by_username(user)
                #get user's posts
                posts = get_all_post_by_user(request,user)
                #get user's liked posts
                post_liked_ids = get_myliked_post(request).values_list("id",flat= True)
                #get user's follow counts
                following_count,follower_count = follow_counts(request,userobj)
                #check if logged user follows or not following the given user
                connect = follow_check(request,userobj)

                return render(request,'network/profile.html',
                {
                "page_info":"other user",
                "username":user,
                "other_user_id":userobj.id,
                "posts":posts,
                "following_count":following_count,
                "follower_count":follower_count,
                "connect":connect,
                "post_liked_ids":post_liked_ids,
                })
            else:
                #user not found
                raise Http404("User Not Found")
    else:
        return HttpResponseRedirect(reverse("network:login"))


def follow_check(request,userobj):

    if request.user.is_authenticated:
        if request.user.username == userobj.username:
            # checking if current user follows itself
            # so sending HttpResponse status code 400- Bad request
            return HttpResponse(status = 400)
        else:
            # get count
            check = len(Follow.objects.filter(follower = request.user.id).filter(following = userobj.id))

            if check > 0:
                return "following"
            return "follow"
    else:
        return HttpResponseRedirect(reverse("network:login"))


def profile_section(request,user,category):
    if request.user.is_authenticated:
        userobj = util.get_user_obj_by_userId(request.user.id)
        # get user's follow counts
        follow = follow_counts(request,userobj)
        post_liked_ids = list(get_myliked_post(request).values_list("id",flat= True))
        if request.method == 'GET':
            if category == "myposts":
                # get user's posts
                myposts = list(get_all_post_by_user(request))
                # dictonary to store results
                result = dict({"myposts":myposts,"post_liked_ids":post_liked_ids})
                # post_liked_ids = get_myliked_post(request).values_list("id",flat= True)

            elif category == "networks":
                following,suggestions = util.get_user_networks(request.user.id)
                # dictonary to store results
                if following == 0:
                    following = 0
                else:
                    following =list(following)

                if suggestions == 0:
                    suggestions = 0
                else:
                    suggestions =list(suggestions)
                result = dict({"following":following,"suggestions":suggestions})
            elif category == "likes":
                post_liked = list(get_myliked_post(request))
                post_liked_user_ids = list(get_myliked_post(request).values_list("user_id",flat= True))
                post_liked_user_id_and_username = User.objects.filter(id__in = set(post_liked_user_ids)).values_list("id","username")
                post_liked_user_id_and_username = dict(post_liked_user_id_and_username)
                result = dict({"post_liked": post_liked ,"post_liked_ids":post_liked_ids,"post_liked_user_id_and_username":post_liked_user_id_and_username})
            else:
                #not a proper section
                raise Http404("No such section")
            result.update(follow)
        response = json.dumps(result,default=str)

        return HttpResponse(response,content_type = "application/json")
    else:
        return HttpResponseRedirect(reverse("network:login"))

def connect(request,user=""):

    if request.user.is_authenticated:
        section =""
        userobj = util.get_user_obj_by_userId(request.user.id)
        form = forms.updatefollowForm(request.POST)
        if form.is_valid():
            #get user id
            if form.cleaned_data["change"]:
                id = form.cleaned_data.get("change")
            else:
                print("form not valid",form.errors)
            # get value to be changed such as follow or following
            if form.cleaned_data["btn"]:
                value = form.cleaned_data.get("btn")
            else:
                print("form not valid",form.errors)

            if form.cleaned_data["fromSection"]:
                section = form.cleaned_data.get("fromSection")
            else:
                print("form not valid",form.errors)

            #making sure that user does not try to connect itself
            if id == userobj.id :
                return HttpResponse(status = 400)
            #following
            if value == "following":
                followobj = Follow.objects.filter(follower = userobj.id).filter(following = id)
                followobj.delete()

            #follow
            if value == "follow":

                userTobe = User.objects.filter(id = id)
                instance = Follow.objects.create(follower = userobj)
                instance.following.set(userTobe)
        else:
            print("Form not valid",form.errors)


        if section:
            # request came from profile page so redirecting profile view with category.
            # so page redirects back to exact same path
            return HttpResponseRedirect(reverse('network:profile',kwargs={'user':request.user.username,'category':section}))
        if len(user) != 0:
            # request came while user checking on other user profile
            return HttpResponseRedirect(reverse('network:profile',kwargs={'user':user}))
        return HttpResponseRedirect(reverse('network:network'))


    else:
        return HttpResponseRedirect(reverse("network:login"))

def follow_counts(request,userobj):

    following_count = Follow.objects.filter(follower = userobj).count()
    follower_count = Follow.objects.filter(following = userobj).count()


    if request.user.username == userobj.username:

        follow_count = {"following_count":following_count,"follower_count":follower_count}
        return follow_count

    return follower_count,following_count

def get_all_post_by_user(request,required_user = ""):

    if request.user.is_authenticated:
        if required_user:
            username = required_user
        else:
            username = request.user.username


        userobj = util.get_user_obj_by_username(username)
        posts = Post.objects.filter(user_id = userobj.id).order_by('-date_and_time').values()


        return posts
    else:
        return HttpResponseRedirect(reverse("network:login"))

def get_all_posts_of_user_network(request,userobj):

    if request.user.is_authenticated:

        if request.user.username == userobj.username:

            following_ids = Follow.objects.values_list('following',flat= True).filter(follower = request.user.id)
            posts = Post.objects.filter(user_id__in = set(following_ids)).order_by('-date_and_time')

            return posts
    else:
        return HttpResponseRedirect(reverse("network:login"))

def get_myliked_post(request):

    if request.user.is_authenticated:


        userobj = util.get_user_obj_by_userId(request.user.id)

        likeobj = Like.objects.values_list('post',flat=True).filter(user = userobj.id)

        postObj = Post.objects.filter(id__in = set(likeobj)).order_by('-date_and_time').values()

        return postObj
    else:
        return HttpResponseRedirect(reverse("network:login"))

def update_like(request,post_id,user=""):
    if request.user.is_authenticated:

        userobj = util.get_user_obj_by_userId(request.user.id)
        postobj = Post.objects.get(id = post_id)

        #check if post is already liked by user
        user_liked_post_ids = get_myliked_post(request).values_list("id",flat=True)

        if len(user_liked_post_ids) > 0 and len(user_liked_post_ids.filter(id = post_id))>0:
            # user have liked the post so delete like from db

            likeobj = Like.objects.filter(user = userobj.id).filter(post=post_id)
            #delete
            likeobj = likeobj.delete()

            #reduce like count by 1
            postobj.num_of_likes = F('num_of_likes')-1
            postobj.save()

            #generate dictonary
            result = {"type":"remove"}

        else:

            user_to_be = User.objects.filter(id = userobj.id)
            instance = Like.objects.create(post = postobj)
            instance.user.set(user_to_be)

            #add like count by 1
            postobj.num_of_likes = F('num_of_likes')+1
            postobj.save()

            #generate dictonary
            result = {"type":"add"}

        num_of_likes = Post.objects.filter(id = post_id).values_list("num_of_likes",flat=True)

        #add final like count to result
        result["num_of_likes"]=num_of_likes[0]

        # generate response
        response = json.dumps(result,default=str)

        return HttpResponse(response,content_type = "application/json")
    else:

        return HttpResponseRedirect(reverse("network:login"))


def following_posts(request):
    if request.user.is_authenticated:
        userobj = util.get_user_obj_by_userId(request.user.id)
        posts = paginate(request,get_all_posts_of_user_network(request,userobj))
        post_liked_ids = get_myliked_post(request).values_list("id",flat= True)
        return render (request, "network/following.html",{
            "allposts": posts,
            "post_liked_ids":post_liked_ids,
            "following": "active",

        })
    else:
        return HttpResponseRedirect(reverse("network:login"))

def edit_post(request,post_id,user=""):
    if request.user.is_authenticated:

        if (get_all_post_by_user(request).filter(id = post_id)):
            # get content
            content = util.queryset_post_content(post_id)

            if content:
                content = str(content[0])

            response = {"contents":content}
            response = json.dumps(response,default=str)
            return HttpResponse(response,content_type = "application/json")
        else:
            #post was not made by user and other user may be trying get information
            return HttpResponse(status=400)
    else:
        return HttpResponseRedirect(reverse("network:login"))

def save_post(request,post_id,content,user=""):
    if request.user.is_authenticated:
        update_post = util.update_post(post_id,content)
        postobj = update_post.values()
        result = {"result":list(postobj),"post_liked_ids" :list(get_myliked_post(request).values_list("id",flat= True))}
        response = json.dumps(result,default=str)
        return HttpResponse(response,content_type = "application/json")

    else:
        return HttpResponseRedirect(reverse("network:login"))

def delete_post(request,post_id,user=""):
    if request.user.is_authenticated:
        if (util.delete_post(post_id)):
            return HttpResponse(status =200)

        return HttpResponse(status = 400 )
    else:
        return HttpResponseRedirect(reverse("network:login"))

def network(request,request_type=""):
    if request.user.is_authenticated:
        return  render(request,"network/network.html",{
        "request_type":request_type,
        })
    else:
        return HttpResponseRedirect(reverse("network:login"))

def network_section(request,section):

    if request.user.is_authenticated:
        user_id_network_tofind = request.user.id
        following_back = 0
        following,suggestion = util.get_user_networks(user_id_network_tofind)
        if suggestion == 0:
            suggestion = 0
        else:
            suggestion = list(suggestion)

        follower_ids = util.get_follower_ids(user_id_network_tofind)
        if follower_ids !=0 and following !=0:
            #following_back - for current user checking on their own  profile
            following_back = following.filter(id__in = set(follower_ids))
            if following_back != 0:
                following_back = list(following_back)


        if following == 0:
            following = 0
        else:
            following = list(following)

        #follower's id with name
        followers = User.objects.filter(id__in = set(follower_ids)).values("id","username")

        if followers == 0:
            followers = 0
        else:
            followers = list(followers)

        result = dict({"following":following,"suggestions":suggestion,"followers":followers,"following_back": following_back})
        response = json.dumps(result,default=str)
        return HttpResponse(response,content_type = "application/json")
