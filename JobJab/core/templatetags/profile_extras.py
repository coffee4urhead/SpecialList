from django import template

register = template.Library()

@register.filter
def profile_picture_url(user):
    if user.profile_picture:
        return user.profile_picture.url
    return '/static/images/avatar-default-photo.png'
