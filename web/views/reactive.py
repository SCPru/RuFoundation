import json
from django.http import HttpResponse

from renderer import render_template_from_string
from renderer.utils import render_user_to_json


def reactive_view(request, *args, **kwargs):
    config = {
        'user': render_user_to_json(request.user)
    }

    return HttpResponse(
        
        render_template_from_string(
        """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <link rel="stylesheet" type="text/css" href="/-/static/fontawesome/css/all.css">
                <link rel="stylesheet" type="text/css" href="/-/static/wikidot-base.css">
                <link rel="stylesheet" type="text/css" href="/-/static/scp-base.css">
                <link rel="stylesheet" type="text/css" href="/-/static/app.css">
                <script src="/-/static/app.js" type="text/javascript"></script>
            </head>
            <body>
                <div id="reactive-root" data-config="{{ config }}"></div>
                <div id="w-modals"></div>
            </body>
            </html>
        """,
        config=json.dumps(config)
    ))