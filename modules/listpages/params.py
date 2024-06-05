from typing import Type, TypeVar

import calendar
from datetime import datetime, timezone

from web.controllers import articles
from system.models import User
from web.models.articles import Article, Tag
from . import param


T = TypeVar('T')


def split_arg_operator(arg, allowed, default):
    for op in allowed:
        if arg.startswith(op):
            return op, arg[len(op):]
    return default, arg


def find_tags_by_incomplete_name(name):
    if ':' in name:
        category, name = articles.get_name(name)
        return list(Tag.objects.filter(category__slug=category, name=name)) or [None]
    return list(Tag.objects.filter(name=name)) or [None]


class ListPagesParams:
    def __init__(self, article: Article = None, viewer: User = None, params: dict = None, path_params: dict = None):
        if params is None:
            params = dict()
        if path_params is None:
            path_params = dict()

        self.params = []

        if params.get('name') == '.' or params.get('range') == '.' or params.get('fullname') == '.':
            if article:
                self.params = [param.Article(article=article)]
            else:
                self.params = [param.Invalid()]
            return

        if params.get('fullname'):
            self.params = [param.FullName(full_name=params.get('fullname'))]
            return

        f_type = params.get('pagetype', 'normal')
        if f_type in ['normal', 'hidden']:
            self.params.append(param.Type(type=f_type))

        f_name = params.get('name', '*')
        if f_name != '*':
            f_name = f_name.replace('%', '*').lower()
            if f_name == '=':
                if article:
                    self.params.append(param.Name(name=article.name))
                else:
                    self.params.append(param.Invalid())
            elif '*' in f_name:
                up_to = f_name.index('*')
                self.params.append(param.NamePrefix(prefix=f_name[:up_to]))
            else:
                self.params.append(param.Name(name=f_name))

        f_tags = params.get('tags', '*')
        if f_tags != '*':
            f_tags = f_tags.replace(',', ' ').lower()
            if f_tags == '-':
                self.params.append(param.NoTags())
            elif f_tags == '=':
                if not article:
                    self.params.append(param.Invalid())
                else:
                    article_tags = article.tags.prefetch_related('category')
                    self.params.append(param.Tags(required=article_tags, present=[], absent=[]))
            elif f_tags == '==':
                if not article:
                    self.params.append(param.Invalid())
                else:
                    article_tags = article.tags.prefetch_related('category')
                    self.params.append(param.ExactTags(tags=article_tags))
            else:
                f_tags = [x.strip() for x in f_tags.split(' ') if x.strip()]
                present_tags = []
                required_tags = []
                absent_tags = []
                for tag in f_tags:
                    if tag[0] == '-':
                        absent_tags.extend(find_tags_by_incomplete_name(tag[1:]))
                    elif tag[0] == '+':
                        required_tags.extend(find_tags_by_incomplete_name(tag[1:]))
                    else:
                        present_tags.extend(find_tags_by_incomplete_name(tag))
                if None in required_tags:
                    self.params.append(param.Invalid())
                elif not [x for x in present_tags if x is not None] and present_tags:
                    self.params.append(param.Invalid())
                else:
                    present_tags = [x for x in present_tags if x is not None]
                    absent_tags = [x for x in absent_tags if x is not None]
                    required_tags = [x for x in required_tags if x is not None]
                    self.params.append(param.Tags(required=required_tags, present=present_tags, absent=absent_tags))

        f_category = params.get('category', '.')
        if f_category != '*':
            f_category = f_category.replace(',', ' ').lower()
            if f_category == '.':
                if article:
                    self.params.append(param.Category(allowed=[article.category], not_allowed=[]))
                else:
                    self.params.append(param.Invalid())
            else:
                categories = []
                not_allowed = []
                for category in f_category.split(' '):
                    category = category.split(':', 1)[0]
                    if not category:
                        continue
                    if category == '.':
                        if not article:
                            continue
                        category = article.category
                    if category[0] == '-':
                        not_allowed.append(category[1:])
                    else:
                        categories.append(category)
                self.params.append(param.Category(allowed=categories, not_allowed=not_allowed))

        f_parent = params.get('parent')
        if f_parent:
            if f_parent == '-':
                self.params.append(param.Parent(parent=None))
            elif f_parent == '=':
                self.params.append(param.Parent(parent=article.parent if article else None))
            elif f_parent == '-=':
                self.params.append(param.NotParent(parent=article.parent if article else None))
            elif f_parent == '.':
                if not article:
                    self.params.append(param.Invalid())
                else:
                    self.params.append(param.Parent(parent=article))
            else:
                parent_article = articles.get_article(f_parent)
                if not parent_article:
                    self.params.append(param.Invalid())
                else:
                    self.params.append(param.Parent(parent=parent_article))

        f_created_by = params.get('created_by')
        if f_created_by:
            if f_created_by == '.':
                user = viewer
            else:
                f_created_by = f_created_by.strip()
                if f_created_by.startswith('wd:'):
                    user = User.objects.filter(type=User.UserType.Wikidot, wikidot_username__iexact=f_created_by[3:])
                else:
                    user = User.objects.filter(username__iexact=f_created_by.strip())
                user = user[0] if user else None
            if not user or not user.is_authenticated:
                self.params.append(param.Invalid())
            else:
                self.params.append(param.CreatedBy(user=user))

        f_created_at = params.get('created_at')
        if f_created_at:
            if f_created_at.strip() == '=':
                if article:
                    day_start = article.created_at.replace(hour=0, minute=0, second=0, microsecond=0)
                    day_end = day_start.replace(hour=23, minute=59, second=59, microsecond=0)
                    self.params.append(param.CreatedAt(type='range', start=day_start, end=day_end))
                else:
                    self.params.append(param.Invalid())
            else:
                op, f_created_at = split_arg_operator(f_created_at, ['>=', '<=', '<>', '>', '<', '='], '=')
                f_created_at = f_created_at.strip()
                try:
                    dd = f_created_at.split('-')
                    year = int(dd[0])
                    first_date = datetime(year=year, month=1, day=1, tzinfo=timezone.utc)
                    last_date = datetime(year=year, month=12, day=31, tzinfo=timezone.utc)
                    if len(dd) >= 2:
                        month = int(dd[1])
                        month = max(1, min(12, month))
                        first_date = first_date.replace(month=month)
                        max_days = calendar.monthrange(year, month)[1]
                        last_date = last_date.replace(month=month, day=max_days)
                    else:
                        month = None  # this is just to silence pycharm
                    if len(dd) >= 3:
                        day = int(dd[2])
                        max_days = calendar.monthrange(year, month)[1]
                        day = max(1, min(max_days, day))
                        first_date = first_date.replace(day=day)
                        last_date = last_date.replace(day=day)
                    if op == '=':
                        self.params.append(param.CreatedAt(type='range', start=first_date, end=last_date))
                    elif op == '<>':
                        self.params.append(param.CreatedAt(type='exclude_range', start=first_date, end=last_date))
                    elif op == '<':
                        self.params.append(param.CreatedAt(type='lt', start=first_date, end=last_date))
                    elif op == '>':
                        self.params.append(param.CreatedAt(type='gt', start=first_date, end=last_date))
                    elif op == '<=':
                        self.params.append(param.CreatedAt(type='lte', start=first_date, end=last_date))
                    elif op == '>=':
                        self.params.append(param.CreatedAt(type='gte', start=first_date, end=last_date))
                    else:
                        raise ValueError(op)
                except:
                    self.params.append(param.Invalid())

        f_rating = params.get('rating')
        if f_rating:
            if f_rating.strip() == '=':
                if article is None:
                    self.params.append(param.Invalid())
                else:
                    current_rating, votes, popularity, mode = articles.get_rating(article)
                    self.params.append(param.Rating(type='eq', rating=current_rating))
            else:
                op, f_rating = split_arg_operator(f_rating, ['>=', '<=', '<>', '>', '<', '='], '=')
                f_rating = f_rating.strip()
                try:
                    try:
                        i_rating = int(f_rating)
                    except ValueError:
                        i_rating = float(f_rating)
                    if op == '=':
                        self.params.append(param.Rating(type='eq', rating=i_rating))
                    elif op == '<>':
                        self.params.append(param.Rating(type='ne', rating=i_rating))
                    elif op == '<':
                        self.params.append(param.Rating(type='lt', rating=i_rating))
                    elif op == '>':
                        self.params.append(param.Rating(type='gt', rating=i_rating))
                    elif op == '<=':
                        self.params.append(param.Rating(type='lte', rating=i_rating))
                    elif op == '>=':
                        self.params.append(param.Rating(type='gte', rating=i_rating))
                    else:
                        raise ValueError(op)
                except:
                    self.params.append(param.Invalid())

        f_votes = params.get('votes')
        if f_votes:
            if f_votes.strip() == '=':
                if article is None:
                    self.params.append(param.Invalid())
                else:
                    current_rating, votes, popularity, mode = articles.get_rating(article)
                    self.params.append(param.Votes(type='eq', votes=votes))
            else:
                op, f_votes = split_arg_operator(f_votes, ['>=', '<=', '<>', '>', '<', '='], '=')
                f_votes = f_votes.strip()
                try:
                    i_votes = int(f_votes)
                    if op == '=':
                        self.params.append(param.Votes(type='eq', votes=i_votes))
                    elif op == '<>':
                        self.params.append(param.Votes(type='ne', votes=i_votes))
                    elif op == '<':
                        self.params.append(param.Votes(type='lt', votes=i_votes))
                    elif op == '>':
                        self.params.append(param.Votes(type='gt', votes=i_votes))
                    elif op == '<=':
                        self.params.append(param.Votes(type='lte', votes=i_votes))
                    elif op == '>=':
                        self.params.append(param.Votes(type='gte', votes=i_votes))
                    else:
                        raise ValueError(op)
                except:
                    self.params.append(param.Invalid())

        f_popularity = params.get('popularity')
        if f_popularity:
            if f_popularity.strip() == '=':
                if article is None:
                    self.params.append(param.Invalid())
                else:
                    current_rating, votes, popularity, mode = articles.get_rating(article)
                    self.params.append(param.Popularity(type='eq', popularity=popularity))
            else:
                op, f_popularity = split_arg_operator(f_popularity, ['>=', '<=', '<>', '>', '<', '='], '=')
                f_popularity = f_popularity.strip()
                try:
                    i_popularity = int(f_popularity)
                    if op == '=':
                        self.params.append(param.Popularity(type='eq', popularity=i_popularity))
                    elif op == '<>':
                        self.params.append(param.Popularity(type='ne', popularity=i_popularity))
                    elif op == '<':
                        self.params.append(param.Popularity(type='lt', popularity=i_popularity))
                    elif op == '>':
                        self.params.append(param.Popularity(type='gt', popularity=i_popularity))
                    elif op == '<=':
                        self.params.append(param.Popularity(type='lte', popularity=i_popularity))
                    elif op == '>=':
                        self.params.append(param.Popularity(type='gte', popularity=i_popularity))
                    else:
                        raise ValueError(op)
                except:
                    self.params.append(param.Invalid())

        f_sort = params.get('order', 'created_at desc').split(' ')
        direction = 'desc' if f_sort[1:] == ['desc'] else 'asc'
        self.params.append(param.Sort(column=f_sort[0], direction=direction))

        try:
            f_offset = int(params.get('offset', '0'))
            self.params.append(param.Offset(offset=f_offset))
        except:
            pass

        try:
            f_limit = int(params.get('limit'))
            self.params.append(param.Limit(limit=f_limit))
        except:
            pass

        try:
            try:
                f_per_page = int(params.get('perpage', '20'))
            except:
                f_per_page = 20
            try:
                f_page = int(path_params.get('p', '1'))
                if f_page < 1:
                    f_page = 1
            except:
                f_page = 1
            self.params.append(param.Pagination(page=f_page, per_page=f_per_page))
        except:
            pass

    def get_type(self, checked_type: Type[T]) -> list[T]:
        return [x for x in self.params if isinstance(x, checked_type)]

    def has_type(self, checked_type: Type[any]):
        matched = self.get_type(checked_type)
        return bool(matched)

    def is_valid(self):
        return not self.has_type(param.Invalid)