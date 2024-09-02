import re

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

def list_entries():
    _, filenames = default_storage.listdir("entries")
    return list(
        sorted(
            re.sub(r"\.md$", "", filename)
            for filename in filenames
            if filename.endswith(".md")
        )
    )


def save_entry(title, content):
    filename = f"entries/{title}.md"
    if default_storage.exists(filename):
        default_storage.delete(filename)
        print(f"Fil exists...delete {filename}")
    default_storage.save(filename, ContentFile(content))

def delete_entry(title):
    filename = f"entries/{title}.md"
    if default_storage.exists(filename):
        return default_storage.delete(filename)

def get_entry(title):

    try:
        f = default_storage.open("entries/{}.md".format(title))
        return f.read().decode("utf-8")
    except FileNotFoundError:
        return None
