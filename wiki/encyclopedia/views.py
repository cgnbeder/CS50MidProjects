import random
import markdown2
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render as _render, redirect
from django.contrib import messages
from django.urls import reverse
from functools import wraps
from . import util


def render(req, url, extra={}):
    alphabet_list = list(map(chr, range(65, 65 + 26)))
    extra.update(entries_options=util.list_entries(),
    alphabet_list=alphabet_list,
    debug=settings.DEBUG)

    return _render(req, url, extra)


def referred_message(req, url, msg, level="success"):
    referred_url = req.META.get("HTTP_REFERER")
    if referred_url and url in referred_url:
        msg_type = getattr(messages, level, None)
        if msg_type:
            msg_type(req, msg)


def index(request):
    entry_list = util.list_entries()
    if request.method == "POST":
        search = request.POST.get("search")
        if search is not None:
            search = search.lower().strip()
            for entry in entry_list:
                if search == entry.lower():
                    return redirect("wiki_entry", title=entry)

            entry_list = list(filter(lambda x: search in x.lower(), entry_list))
            if not entry_list:
                return redirect(notFound)

    context = {"entries": entry_list}
    return render(request, "encyclopedia/index.html", context)


def wiki_entry(request, title):
    context = {}
    entry_list = util.list_entries()

    title = title.strip()
    wiki = [entry for entry in entry_list if title.lower() in entry.lower()]

    if not wiki or wiki is None:
        return redirect(notFound)

    entry = util.get_entry(wiki[0])
    context["title"] = title
    context["entry"] = markdown2.markdown(entry).strip()
    return render(request, "encyclopedia/base_entry.html", context)


def saveHandler(request, **kwargs):


    title = kwargs.get("title", "")
    content = kwargs.get("content", "")
    if content and title:
        title = title.strip()
        entry = util.save_entry(title.strip(), str(content).strip())
        return redirect("wiki_entry", title=title)
    return redirect(notFound)


def create_update(request, title=""):

    context = {"config": "create"}
    previous_title = title
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        submit = request.POST.get("submit")
        hidden = request.POST.get("config")

        if submit is None:
            if "create" in hidden:
                return redirect(index)
            else:
                return redirect(reverse("wiki_entry", kwargs={"title": title}))

        elif not title or not content:
            messages.warn(
                request, f" You must add a title and content to create entry!"
            )
            return render(request, "encyclopedia/create_edit_entry.html", context)

        action = "updated" if "edit" in hidden else "created"
        if action == "updated":
            util.delete_entry(previous_title)
        messages.success(request, f" Your entry was {action} successfully!")
        return saveHandler(request, title=title, content=content)

    else:
        context = {"config": "create"}
        if title:
            entry = util.get_entry(title)
            if not entry or entry is None:
                return redirect(notFound)
            context["entry"] = entry
            context["config"] = "edit"

        context.update(
            {
                "title": title,
                "unavailable_entry": util.list_entries(),
            }
        )

    return render(request, "encyclopedia/create_edit_entry.html", context)


def random_entry(request):

    entry_list = util.list_entries()
    if entry_list:
        rand_entry = random.choices(entry_list)[0]
        return HttpResponseRedirect(reverse("wiki_entry", args=(rand_entry,)))

    messages.error(request, f"Opp... Something went wrong!")

    return redirect(index)


def delete_entry(request, title, deletion=None):
    context = {}
    if deletion:
        if title:
            if deletion == "delete":
                util.delete_entry(title)
                messages.error(request, f"{title} was deleted.")
                return redirect("index")
            else:
                messages.warning(request, f"Deleting was cancel {title}.")
                return redirect("wiki_entry", title=title)

    context["title"] = title
    return render(request, "encyclopedia/delete_entry.html", context)


def notFound(request):
    return render(request, "encyclopedia/notfound.html")
