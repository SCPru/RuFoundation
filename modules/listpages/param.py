from typing import Literal
from web.models.users import User
from datetime import datetime
import web.models.articles


class Invalid:
    pass


class Article:
    def __init__(self, article: web.models.articles.Article | None):
        self.article = article


class FullName:
    def __init__(self, full_name: str):
        self.full_name = full_name


class Range:
    def __init__(self, article_range: str):
        self.range = article_range


class Type:
    def __init__(self, type: Literal['normal', 'hidden']):
        self.type = type


class Name:
    def __init__(self, name: str):
        self.name = name


class NamePrefix:
    def __init__(self, prefix: str):
        self.prefix = prefix


class NoTags:
    pass


class ExactTags:
    def __init__(self, tags: list[web.models.articles.Tag]):
        self.tags = tags


class Tags:
    def __init__(self, required: list[web.models.articles.Tag], present: list[web.models.articles.Tag], absent: list[web.models.articles.Tag]):
        self.type = type
        self.required = required
        self.present = present
        self.absent = absent


class Category:
    def __init__(self, allowed: list[str], not_allowed: list[str]):
        self.allowed = allowed
        self.not_allowed = not_allowed


class Parent:
    def __init__(self, parent: web.models.articles.Article | None):
        self.parent = parent


class NotParent:
    def __init__(self, parent: web.models.articles.Article | None):
        self.parent = parent


class CreatedBy:
    def __init__(self, user: User):
        self.user = user


class CreatedAt:
    def __init__(self, type: Literal['range', 'exclude_range', 'lt', 'lte', 'gt', 'gte'], start: datetime, end: datetime):
        self.type = type
        self.start = start
        self.end = end


class Rating:
    def __init__(self, type: Literal['eq', 'ne', 'lt', 'lte', 'gt', 'gte'], rating: int | float):
        self.type = type
        self.rating = rating


class Votes:
    def __init__(self, type: Literal['eq', 'ne', 'lt', 'lte', 'gt', 'gte'], votes: int):
        self.type = type
        self.votes = votes


class Popularity:
    def __init__(self, type: Literal['eq', 'ne', 'lt', 'lte', 'gt', 'gte'], popularity: int):
        self.type = type
        self.popularity = popularity


class Sort:
    def __init__(self, column: str, direction: Literal['asc', 'desc']):
        self.column = column
        self.direction = direction


class Offset:
    def __init__(self, offset: int):
        self.offset = offset


class Limit:
    def __init__(self, limit: int):
        self.limit = limit


class Pagination:
    def __init__(self, page: int, per_page: int):
        self.page = page
        self.per_page = per_page
