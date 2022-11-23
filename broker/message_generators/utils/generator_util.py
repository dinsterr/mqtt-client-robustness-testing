import unicodedata

# only use unicode categories that don't include control codes
unicode_glyphs = ''.join(chr(char) for char in range(65533) if unicodedata.category(chr(char))[0] in 'LMNPSZ')
