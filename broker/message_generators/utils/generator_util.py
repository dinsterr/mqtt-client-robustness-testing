import unicodedata
import random
import string

_MAX_PAYLOAD_CHARS = 1024

# only use unicode categories that don't include control codes
unicode_glyphs = ''.join(chr(char) for char in range(65533) if unicodedata.category(chr(char))[0] in 'LMNPSZ')


def random_unicode_string(lower_limit=0, upper_limit=_MAX_PAYLOAD_CHARS):
    rand_length = random.randint(lower_limit, upper_limit)
    return ''.join([random.choice(unicode_glyphs)
                    for _ in range(rand_length)])


def random_ascii_string(lower_limit=0, upper_limit=_MAX_PAYLOAD_CHARS):
    rand_length = random.randint(lower_limit, upper_limit)
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(rand_length))
