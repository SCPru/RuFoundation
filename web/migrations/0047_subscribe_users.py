# Generated by Django 5.1.4 on 2025-04-17 17:14

from django.db import migrations


def subscribe_users(apps, schema_editor):
    Article = apps.get_model("web", "Article")
    ForumThread = apps.get_model("web", "ForumThread")
    UserNotificationSubscription = apps.get_model("web", "UserNotificationSubscription")

    all_subscriptions = []

    for article in Article.objects.all():
        if not article.author_id:
            continue
        all_subscriptions.append(
            UserNotificationSubscription(
                subscriber=article.author,
                article=article,
                forum_thread=None
            )
        )
        article_comments = ForumThread.objects.filter(article=article)
        for comment_thread in article_comments:
            all_subscriptions.append(
                UserNotificationSubscription(
                    subscriber=article.author,
                    article=None,
                    forum_thread=comment_thread
                )
            )

    for forum_thread in ForumThread.objects.all():
        if not forum_thread.author_id:
            continue
        all_subscriptions.append(
            UserNotificationSubscription(
                subscriber=forum_thread.author,
                article=None,
                forum_thread=forum_thread
            )
        )

    UserNotificationSubscription.objects.bulk_create(all_subscriptions)


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0046_usernotification_usernotificationtemplate_and_more'),
    ]

    operations = [
        migrations.RunPython(subscribe_users),
    ]
