from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from modules import rate
from web.controllers import articles
from web.models.settings import Settings


class RatingVisibilityTests(SimpleTestCase):
    def make_article(self, visibility_mode):
        article = MagicMock()
        article.settings.rating_visibility_mode = visibility_mode
        return article

    @patch.object(articles, 'get_article')
    def test_always_mode_is_visible_without_vote(self, get_article):
        article = self.make_article(Settings.RatingVisibilityMode.Always)
        user = MagicMock(is_anonymous=True)
        get_article.return_value = article

        self.assertFalse(articles.is_rating_hidden(article, user))
        user.has_perm.assert_not_called()
        article.votes.filter.assert_not_called()

    @patch.object(articles, 'get_article')
    def test_after_vote_mode_is_hidden_from_anonymous_viewer(self, get_article):
        article = self.make_article(Settings.RatingVisibilityMode.AfterVote)
        user = MagicMock(is_anonymous=True)
        user.has_perm.return_value = False
        get_article.return_value = article

        self.assertTrue(articles.is_rating_hidden(article, user))
        article.votes.filter.assert_not_called()

    @patch.object(articles, 'get_article')
    def test_after_vote_mode_is_visible_to_voter(self, get_article):
        article = self.make_article(Settings.RatingVisibilityMode.AfterVote)
        user = MagicMock(is_anonymous=False)
        user.has_perm.return_value = False
        article.votes.filter.return_value.exists.return_value = True
        get_article.return_value = article

        self.assertFalse(articles.is_rating_hidden(article, user))
        article.votes.filter.assert_called_once_with(user=user)

    @patch.object(articles, 'get_article')
    def test_bypass_permission_ignores_visibility_mode(self, get_article):
        article = self.make_article(Settings.RatingVisibilityMode.AfterVote)
        user = MagicMock(is_anonymous=False)
        user.has_perm.return_value = True
        get_article.return_value = article

        self.assertFalse(articles.is_rating_hidden(article, user))
        user.has_perm.assert_called_once_with('roles.bypass_rating_visibility', article)
        article.votes.filter.assert_not_called()

    @patch.object(articles, 'is_rating_hidden', return_value=True)
    @patch.object(articles, 'get_rating', return_value=(4.7, 18, 83, Settings.RatingMode.Stars))
    def test_visible_rating_does_not_expose_hidden_values(self, get_rating, is_rating_hidden):
        self.assertEqual(
            articles.get_visible_rating(MagicMock(), MagicMock()),
            (0, 0, 0, Settings.RatingMode.Stars, True),
        )

    @patch.object(rate.articles, 'get_visible_rating', return_value=(0, 0, 0, Settings.RatingMode.Stars, True))
    def test_votes_api_does_not_query_or_return_hidden_votes(self, get_visible_rating):
        article = SimpleNamespace(full_name='test')
        context = SimpleNamespace(article=article, user=MagicMock())

        with patch.object(rate.Vote, 'objects') as vote_objects:
            response = rate.api_get_votes(context, {})

        self.assertTrue(response['ratingHidden'])
        self.assertEqual(response['votes'], [])
        self.assertEqual(response['rating'], 0)
        self.assertEqual(response['popularity'], 0)
        vote_objects.filter.assert_not_called()
