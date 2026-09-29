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
        article = SimpleNamespace(full_name='test', settings=Settings(rating_visibility_mode=Settings.RatingVisibilityMode.AfterVote))
        context = SimpleNamespace(article=article, user=MagicMock())

        with patch.object(rate.Vote, 'objects') as vote_objects:
            response = rate.api_get_votes(context, {})

        self.assertTrue(response['ratingHidden'])
        self.assertEqual(response['votes'], [])
        self.assertEqual(response['rating'], 0)
        self.assertEqual(response['popularity'], 0)
        vote_objects.filter.assert_not_called()

    @patch.object(articles, 'get_article')
    def test_hidden_mode_stays_hidden_after_voting(self, get_article):
        article = self.make_article(Settings.RatingVisibilityMode.Hidden)
        user = MagicMock(is_anonymous=False)
        user.has_perm.return_value = False
        article.votes.filter.return_value.exists.return_value = True
        get_article.return_value = article

        self.assertTrue(articles.is_rating_hidden(article, user))
        article.votes.filter.assert_not_called()
        self.assertTrue(articles.should_hide_rating(Settings.RatingVisibilityMode.Hidden, has_voted=True, can_bypass=False))

    @patch.object(articles, 'get_article')
    def test_hidden_mode_respects_bypass_permission(self, get_article):
        article = self.make_article(Settings.RatingVisibilityMode.Hidden)
        user = MagicMock(is_anonymous=False)
        user.has_perm.return_value = True
        get_article.return_value = article

        self.assertFalse(articles.is_rating_hidden(article, user))
        user.has_perm.assert_called_once_with('roles.bypass_rating_visibility', article)

    def test_hidden_mode_tooltip_does_not_promise_reveal_after_vote(self):
        article = self.make_article(Settings.RatingVisibilityMode.Hidden)
        self.assertEqual(articles.get_rating_hidden_tooltip(article), 'Рейтинг скрыт настройками категории')

    def test_own_vote_query_is_scoped_to_viewer_and_preserves_zero(self):
        article = self.make_article(Settings.RatingVisibilityMode.Hidden)
        user = MagicMock(is_anonymous=False)
        with patch.object(rate.Vote, 'objects') as objects:
            objects.filter.return_value.values_list.return_value.first.return_value = 0
            self.assertEqual(rate.get_own_vote(article, user), 0)
            objects.filter.assert_called_once_with(article=article, user=user)
            objects.filter.return_value.values_list.assert_called_once_with('rate', flat=True)

    def test_anonymous_viewer_has_no_own_vote(self):
        with patch.object(rate.Vote, 'objects') as objects:
            self.assertIsNone(rate.get_own_vote(MagicMock(), MagicMock(is_anonymous=True)))
            self.assertIsNone(rate.get_own_vote(MagicMock(), None))
            objects.filter.assert_not_called()

    @patch.object(rate.articles, 'get_visible_rating', return_value=(0, 0, 0, Settings.RatingMode.Stars, True))
    def test_hidden_apis_expose_only_own_vote(self, get_visible_rating):
        article = SimpleNamespace(full_name='test', settings=Settings(rating_visibility_mode=Settings.RatingVisibilityMode.Hidden))
        context = SimpleNamespace(article=article, user=MagicMock(is_anonymous=False))
        for own_vote in (4.5, 0, None):
            with self.subTest(own_vote=own_vote), patch.object(rate.Vote, 'objects') as objects:
                objects.filter.return_value.values_list.return_value.first.return_value = own_vote
                rating_response = rate.api_get_rating(context, {})
                votes_response = rate.api_get_votes(context, {})
                for response in (rating_response, votes_response):
                    self.assertEqual(response['ownVote'], own_vote)
                    self.assertEqual(response['ratingVisibilityMode'], Settings.RatingVisibilityMode.Hidden)
                    self.assertTrue(response['ratingHidden'])
                    self.assertEqual(response['rating'], 0)
                    self.assertEqual(response['popularity'], 0)
                self.assertEqual(rating_response['voteCount'], 0)
                self.assertEqual(votes_response['votes'], [])
                for call in objects.filter.call_args_list:
                    self.assertEqual(call.kwargs, {'article': article, 'user': context.user})

    def test_hidden_widgets_render_own_vote_after_reload(self):
        article = SimpleNamespace(full_name='test', settings=Settings(rating_visibility_mode=Settings.RatingVisibilityMode.Hidden))
        context = SimpleNamespace(article=article, user=MagicMock(is_anonymous=False))
        for mode, own_vote, expected in (
            (Settings.RatingMode.Stars, 4.5, 'Ваша оценка: 4.5'),
            (Settings.RatingMode.Stars, 0, 'Ваша оценка: 0.0'),
            (Settings.RatingMode.UpDown, 1, 'Ваша оценка: +1'),
            (Settings.RatingMode.UpDown, -1, 'Ваша оценка: -1'),
        ):
            with self.subTest(mode=mode, own_vote=own_vote), \
                    patch.object(rate.articles, 'get_visible_rating', return_value=(0, 0, 0, mode, True)), \
                    patch.object(rate, 'get_own_vote', return_value=own_vote):
                html = rate.render(context, {})
                self.assertIn(expected, html)
                self.assertIn('w-rating-concealed', html)
                if mode == Settings.RatingMode.Stars:
                    self.assertIn('width: %d%%' % (own_vote * 20), html)

    @patch.object(rate.articles, 'get_visible_rating', return_value=(0, 0, 0, Settings.RatingMode.Stars, True))
    @patch.object(rate, 'get_own_vote', return_value=None)
    def test_hidden_widget_without_vote_has_no_own_vote_label(self, get_own_vote, get_visible_rating):
        article = SimpleNamespace(full_name='test', settings=Settings(rating_visibility_mode=Settings.RatingVisibilityMode.Hidden))
        html = rate.render(SimpleNamespace(article=article, user=None), {})
        self.assertNotIn('Ваша оценка:', html)

    def test_own_vote_replaces_footer_statistics_only_in_hidden_mode_after_vote(self):
        for visibility_mode in Settings.RatingVisibilityMode:
            for own_vote in (None, 0, 4.5):
                for rating_hidden in (False, True):
                    with self.subTest(visibility_mode=visibility_mode, own_vote=own_vote, rating_hidden=rating_hidden):
                        article = SimpleNamespace(full_name='test', settings=Settings(rating_visibility_mode=visibility_mode))
                        context = SimpleNamespace(article=article, user=MagicMock())
                        with patch.object(rate.articles, 'get_visible_rating', return_value=(0, 0, 0, Settings.RatingMode.Stars, rating_hidden)), \
                                patch.object(rate, 'get_own_vote', return_value=own_vote):
                            html = rate.render(context, {})
                        show_own_vote = rating_hidden and visibility_mode == Settings.RatingVisibilityMode.Hidden and own_vote is not None
                        self.assertEqual('Ваша оценка:' in html, show_own_vote)
                        self.assertEqual('w-rate-show-own-vote' in html, show_own_vote)
                        self.assertRegex(html, r'<div class="w-stars-rate-votes">(?:(?!</div>).)*class="w-rate-own-vote"')
