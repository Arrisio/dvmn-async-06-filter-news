from . import inosmi_ru
from . import plain_text
from .exceptions import ArticleNotFound

__all__ = ['SANITIZERS', 'ArticleNotFound']

SANITIZERS = {
    'inosmi.ru': inosmi_ru.sanitize,
    'dvmn.org': plain_text.sanitize,
}
