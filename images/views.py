from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ImageCreateForm
from .models import Image

from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from common.decorators import ajax_required

from actions.utils import create_action

import redis
from django.conf import settings

# connect to redis
r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)


@login_required
def image_create(request):
  if request.method == "POST":
    form = ImageCreateForm(data=request.POST)
    if form.is_valid():
      cd = form.cleaned_data
      new_item = form.save(commit=False)
      # assign current user to the image model
      new_item.user = request.user
      new_item.save()
      create_action(request.user, 'bookmarked image', new_item)
      messages.success(request, "Image added successfully")

      return redirect(new_item.get_absolute_url())

  else:
    form = ImageCreateForm(data=request.GET)

  return render(request, 'images/image/create.html', { 'section': 'images', 'form': form})


def image_detail(request, id, slug):
  image = get_object_or_404(Image, id=id, slug=slug)
  # increment total image views by 1
  total_views = r.incr(f'image:{image.id}:views')
  context = {
    'section': 'images',
    'image': image,
    'total_views': total_views
  }
  return render(request, 'images/image/detail.html', context)


@ajax_required
@login_required
@require_POST
def image_like(request):
  image_id = request.POST.get('id')
  action = request.POST.get('action')
  if image_id and action:
    try:
      image = Image.objects.get(id=image_id)
      if action == 'like':
        image.users_like.add(request.user)
        create_action(request.user, 'likes', image)
      else:
        image.users_like.remove(request.user)
      return JsonResponse({'status': 'ok'})
    except:
      pass
  return JsonResponse({'status': 'ko'})


@login_required
def image_list(request):
  images = Image.objects.all()
  paginator = Paginator(images, 8)
  page = request.GET.get('page')
  try:
    images = paginator.page(page)
  except PageNotAnInteger:
    images = paginator.page(1) # display first page if not an integer
  except EmptyPage:
    if request.is_ajax():
      # if the request is AJAX and the page is out of range
      return HttpResponse('') # return an empty page
    images = paginator.page(paginator.num_pages) # deliver the last page of result if request out of range
  if request.is_ajax():
    return render(request, 'images/image/list_ajax.html', {'section': 'images', 'images': images})
  return render(request, 'images/image/list.html', {'section': 'images', 'images': images})
      

