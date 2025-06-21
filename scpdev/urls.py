"""scpdev URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from django.conf import settings

from web.views.media import MediaView
from web.views.local_code_and_html import LocalCodeView, LocalHTMLView


urlpatterns = [
    path(f"local--files/<path:dir_path>", MediaView.as_view()),
    path(f"local--code/<page_id>/<int:index>", LocalCodeView.as_view()),
    path(f"local--html/<page_id>/<hash_and_id>", LocalHTMLView.as_view()),
    path("", include("web.urls"))
]
