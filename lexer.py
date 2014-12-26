#!/usr/bin/python3
#
# Lexer for twiki parser.

import cgi
import re
import sys

import ll1

# Lexer throws this exception when tokenize fails.
class Error(Exception): pass


# Define a subclass of str so that we can attach line number to it. See:
# http://bytes.com/topic/python/answers/32098-my-experiences-subclassing-string
class String(str):
  def __new__(self, string, line_no):
    return str.__new__(self, string)

  def __init__(self, string, line_no):
    self.line_no = line_no


# Base class for all tokens.
class Token(ll1.Terminal):
  def __init__(self):
    """Initialize standard attributes of a token"""
    # 'value' is the corresponding twiki source for this token.
    self.value = ''

    # 'html' is the html code for this token.
    self.html = ''

    # 'line_no' is the line number of this token.
    self.line_no = 0

  def __str__(self):
    assert self.line_no > 0
    if self.value:
      return '%s at line %s with value %s: %s' % (
          self.__class__, self.line_no, self.value, self.html)
    else:
      return '%s at line %s: %s' % (self.__class__, self.line_no, self.html)

  @staticmethod
  def CreateWithLineNo(token_type, line_no):
    assert line_no > 0
    token = token_type()
    token.line_no = line_no
    return token


class WORD(Token): pass
class PUNCTURE(Token): pass

class BOLD_WORD(Token): pass
class BOLD_START_WORD(Token): pass
class BOLD_END_WORD(Token): pass
class ITALICS_WORD(Token): pass
class ITALICS_START_WORD(Token): pass
class ITALICS_END_WORD(Token): pass
class FIXED_WIDTH_WORD(Token): pass
class FIXED_WIDTH_START_WORD(Token): pass
class FIXED_WIDTH_END_WORD(Token): pass

class SHORT_LINK(Token): pass
class LONG_LINK(Token): pass
class LONG_LINK_START(Token): pass
class LONG_LINK_END(Token): pass
class URL(Token): pass
class IMAGE_LINK(Token): pass

class COLOR_START(Token): pass
class ENDCOLOR(Token): pass

class TITLE_LEAD1(Token): pass
class TITLE_LEAD2(Token): pass
class TITLE_LEAD3(Token): pass
class TITLE_LEAD4(Token): pass
class TITLE_LEAD5(Token): pass
class TITLE_LEAD6(Token): pass

class UNORDERED_LIST_LEAD1(Token): pass
class UNORDERED_LIST_LEAD2(Token): pass
class UNORDERED_LIST_LEAD3(Token): pass
class UNORDERED_LIST_LEAD4(Token): pass
class ORDERED_LIST_LEAD1(Token): pass
class ORDERED_LIST_LEAD2(Token): pass
class ORDERED_LIST_LEAD3(Token): pass
class ORDERED_LIST_LEAD4(Token): pass

class LINE_LEAD_WHITESPACE(Token): pass
class TOC(Token): pass
class VERBATIM(Token): pass
class NEW_LINE(Token): pass


# The implementation is quite strightforward. We keep the parsed tokens and
# unparsed strings in a list and begin with a list of string.  We then scan
# all the elements in the list in several passes. Each pass skips parsed tokens
# and only looks at unparsed strings and generates tokens out of them.
def tokenize(string):
  # Split the input into a list strings.
  token_list = []
  for line_no, line in enumerate(string.splitlines()):
    token_list.append(String(line, line_no+1))

    new_line = Token.CreateWithLineNo(NEW_LINE, line_no+1)
    new_line.value = '\n'
    new_line.html = '\n'
    token_list.append(new_line)

  # since we need to keep all the formatting in <verbatim> as is, we need to
  # parse it first.
  verbatim_processor = VerbatimProcessor()
  new_token_list = []
  for token in token_list:
    new_token_list.extend(verbatim_processor.Do(token))
  token_list = new_token_list
  verbatim_processor.Verify()

  # Recognize all the title_lead, list_lead and line_lead_whitespace.
  new_token_list = []
  for token in token_list:
    new_token_list.extend(ProcessLineLead(token))
  token_list = new_token_list

  # Split line into words by whitespace.
  new_token_list = []
  for token in token_list:
    new_token_list.extend(SplitLineIntoWord(token))
  token_list = new_token_list

  # Recognize punctures.
  new_token_list = []
  for token in token_list:
    new_token_list.extend(ProcessPuncture(token))
  token_list = new_token_list

  # Recognize Wiki variables.
  new_token_list = []
  for token in token_list:
    new_token_list.extend(ProcessVariable(token))
  token_list = new_token_list

  # Convert all the strings into WORD, recognize the special words.
  new_token_list = []
  for token in token_list:
    new_token_list.extend(WordProcessor.Do(token))
  token_list = new_token_list

  return token_list


class VerbatimProcessor(object):
  def __init__(self):
    self.seen_verbatim = False
    self.line_no = 0
    self.content = []

  def Do(self, token):
    if self.seen_verbatim:
      if type(token) == String:
        if token == '</verbatim>':
          self.seen_verbatim = False
          verbatim = Token.CreateWithLineNo(VERBATIM, self.line_no)
          verbatim.value = '\n'.join(self.content)
          verbatim.html = '<pre>\n%s\n</pre>\n' % verbatim.value
          self.content = []
          return [verbatim]
        else:
          self.content.append(token)
          return []
      else:
        assert type(token) == NEW_LINE
        return []
    else:
      if type(token) == String:
        if token == '<verbatim>':
          self.seen_verbatim = True
          self.line_no = token.line_no
          return []
        else:
          return [token]
      else:
        return [token]

  def Verify(self):
    if self.seen_verbatim:
      raise Error('Unbalanced verbatim, start mark seen at %s' % self.line_no)


def ProcessLineLead(token):
  if type(token) != String:
    return [token]

  # Remove empty line. Notice that NEW_LINE has been generated.
  if not token.strip():
    return []

  # Titles.
  if token.startswith('---++++++'):
    return [Token.CreateWithLineNo(TITLE_LEAD6, token.line_no),
            String(token[9:], token.line_no)]
  if token.startswith('---+++++'):
    return [Token.CreateWithLineNo(TITLE_LEAD5, token.line_no),
            String(token[8:], token.line_no)]
  if token.startswith('---++++'):
    return [Token.CreateWithLineNo(TITLE_LEAD4, token.line_no),
            String(token[7:], token.line_no)]
  if token.startswith('---+++'):
    return [Token.CreateWithLineNo(TITLE_LEAD3, token.line_no),
            String(token[6:], token.line_no)]
  if token.startswith('---++'):
    return [Token.CreateWithLineNo(TITLE_LEAD2, token.line_no),
            String(token[5:], token.line_no)]
  if token.startswith('---+'):
    return [Token.CreateWithLineNo(TITLE_LEAD1, token.line_no),
            String(token[4:], token.line_no)]

  # Lists.
  if token.startswith(' '*3 + '* '):
    return [Token.CreateWithLineNo(UNORDERED_LIST_LEAD1, token.line_no),
            String(token[5:], token.line_no)]
  if token.startswith(' '*6 + '* '):
    return [Token.CreateWithLineNo(UNORDERED_LIST_LEAD2, token.line_no),
            String(token[8:], token.line_no)]
  if token.startswith(' '*9 + '* '):
    return [Token.CreateWithLineNo(UNORDERED_LIST_LEAD3, token.line_no),
            String(token[11:], token.line_no)]
  if token.startswith(' '*12 + '* '):
    return [Token.CreateWithLineNo(UNORDERED_LIST_LEAD4, token.line_no),
            String(token[14:], token.line_no)]

  if token.startswith(' '*3 + '1 ') or token.startswith(' '*3 + '# '):
    return [Token.CreateWithLineNo(ORDERED_LIST_LEAD1, token.line_no),
            String(token[5:], token.line_no)]
  if token.startswith(' '*6 + '1 ') or token.startswith(' '*6 + '# '):
    return [Token.CreateWithLineNo(ORDERED_LIST_LEAD2, token.line_no),
            String(token[8:], token.line_no)]
  if token.startswith(' '*9 + '1 ') or token.startswith(' '*9 + '# '):
    return [Token.CreateWithLineNo(ORDERED_LIST_LEAD3, token.line_no),
            String(token[11:], token.line_no)]
  if token.startswith(' '*12 + '1 ') or token.startswith(' '*12 + '# '):
    return [Token.CreateWithLineNo(ORDERED_LIST_LEAD4, token.line_no),
            String(token[14:], token.line_no)]

  # Test line leading whitespace.
  if (token.startswith(' ') or token.startswith('\t')):
    return [Token.CreateWithLineNo(LINE_LEAD_WHITESPACE, token.line_no),
            String(token.lstrip(), token.line_no)]

  # Return token as is.
  return [token]


def SplitLineIntoWord(token):
  if type(token) != String:
    return [token]
  else:
    return [String(new_token, token.line_no) for new_token in token.split()]


def ProcessPuncture(token):
  if type(token) != String:
    return [token]

  #TODO: Add (), {} and [] support.
  if (token.endswith('.') or
      token.endswith(',') or
      token.endswith(';') or
      token.endswith(':') or
      token.endswith('!') or
      token.endswith('?')):
    puncture = Token.CreateWithLineNo(PUNCTURE, token.line_no)
    puncture.value = token[-1:]
    puncture.html = puncture.value
    return [String(token[0:-1], token.line_no), puncture]
  else:
    return [token]


def ProcessVariable(token):
  if type(token) != String:
    return [token]

  if token == '%RED%' or token == '%BLUE%' or token == '%GREEN%':
    color_start = Token.CreateWithLineNo(COLOR_START, token.line_no)
    color_start.value = token
    color_start.html = "<font color='%s'>" % token[1:-1]
    return [color_start]

  if token == '%ENDCOLOR%':
    end_color = Token.CreateWithLineNo(ENDCOLOR, token.line_no)
    end_color.value = token
    end_color.html = '</font>'
    return [end_color]

  if token == '%TOC%':
    toc = Token.CreateWithLineNo(TOC, token.line_no)
    toc.value = token
    toc.html = '<toc/>'
    return [toc]

  return [token]


# Use a class to avoid compiling regular expression multiple times.
class WordProcessor(object):
  short_link_regexp = re.compile(r'\[\[(?! )([^]]+)(?<! )\]\]')
  image_link_regexp = re.compile(r'\[\[(?! )([^]]+)(?<! )\]\[%IMAGE(.*)%\]\]')
  long_link_regexp = \
      re.compile(r'\[\[(?! )([^]]+)(?<! )\]\[(?! )([^]]+)(?<! )\]\]')
  long_link_start_regexp = re.compile(r'\[\[([^]]+)\]\[([^]]+)')
  long_link_end_regexp = re.compile(r'([^]]+)\]\]')
  url_regexp = re.compile(r'((http://)|(https://)|(mailto://)|(ftp://)).+')

  @staticmethod
  def Do(token):
    if type(token) != String:
      return [token]

    if token.startswith('*') and token.endswith('*'):
      bold_word = Token.CreateWithLineNo(BOLD_WORD, token.line_no)
      bold_word.value = token
      bold_word.html = "<b>%s</b>" % cgi.escape(token[1:-1])
      return [bold_word]

    if token.startswith('*'):
      bold_start_word = Token.CreateWithLineNo(BOLD_START_WORD, token.line_no)
      bold_start_word.value = token
      bold_start_word.html = "<b>" + cgi.escape(token[1:])
      return [bold_start_word]

    if token.endswith('*'):
      bold_end_word = Token.CreateWithLineNo(BOLD_END_WORD, token.line_no)
      bold_end_word.value = token
      bold_end_word.html = cgi.escape(token[:-1]) + "</b>"
      return [bold_end_word]

    if token.startswith('_') and token.endswith('_'):
      italics_word = Token.CreateWithLineNo(ITALICS_WORD, token.line_no)
      italics_word.value = token
      italics_word.html = "<i>%s</i>" % cgi.escape(token[1:-1])
      return [italics_word]

    if token.startswith('_'):
      italics_start_word = Token.CreateWithLineNo(ITALICS_START_WORD,
                                                  token.line_no)
      italics_start_word.value = token
      italics_start_word.html = "<i>" + cgi.escape(token[1:])
      return [italics_start_word]

    if token.endswith('_'):
      italics_end_word = Token.CreateWithLineNo(ITALICS_END_WORD, token.line_no)
      italics_end_word.value = token
      italics_end_word.html = cgi.escape(token[:-1]) + "</i>"
      return [italics_end_word]

    if token.startswith('=') and token.endswith('='):
      fixed_width_word = Token.CreateWithLineNo(FIXED_WIDTH_WORD, token.line_no)
      fixed_width_word.value = token
      fixed_width_word.html = "<code>%s</code>" % cgi.escape(token[1:-1])
      return [fixed_width_word]

    if token.startswith('='):
      fixed_width_start_word = Token.CreateWithLineNo(FIXED_WIDTH_START_WORD,
                                                      token.line_no)
      fixed_width_start_word.value = token
      fixed_width_start_word.html = "<code>" + cgi.escape(token[1:])
      return [fixed_width_start_word]

    if token.endswith('='):
      fixed_width_end_word = Token.CreateWithLineNo(FIXED_WIDTH_END_WORD,
                                                    token.line_no)
      fixed_width_end_word.value = token
      fixed_width_end_word.html = cgi.escape(token[:-1]) + "</code>"
      return [fixed_width_end_word]

    # TODO: We should have a clearer rule what is allowed in wiki-word.
    match_object = WordProcessor.short_link_regexp.match(token)
    if match_object:
      wiki_word = cgi.escape(match_object.group(1).replace(r'"', r'_'))

      short_link = Token.CreateWithLineNo(SHORT_LINK, token.line_no)
      short_link.value = token
      short_link.html = "<a href='/pwdoc/ViewPage/%s'>%s</a>" % (wiki_word,
                                                                 wiki_word,)
      short_link.wiki_word = wiki_word
      return [short_link]

    match_object = WordProcessor.image_link_regexp.match(token)
    if match_object:
      link = match_object.group(1)

      attribute_list = []
      for attribute in match_object.group(2).split(':'):
        if attribute:
          attribute_list.append(attribute)

      image_link = Token.CreateWithLineNo(IMAGE_LINK, token.line_no)
      image_link.value = token
      image_link.html = "<img src='%s' %s/>" % (link, ' '.join(attribute_list))
      return [image_link]

    match_object = WordProcessor.long_link_regexp.match(token)
    if match_object:
      link = match_object.group(1)
      word = cgi.escape(match_object.group(2))

      long_link = Token.CreateWithLineNo(LONG_LINK, token.line_no)
      long_link.value = token
      long_link.html = "<a href='%s'>%s</a>" % (link, word)
      long_link.link = link
      return [long_link]

    match_object = WordProcessor.long_link_start_regexp.match(token)
    if match_object:
      link = match_object.group(1)
      word = cgi.escape(match_object.group(2))

      long_link_start = Token.CreateWithLineNo(LONG_LINK_START, token.line_no)
      long_link_start.value = token
      long_link_start.html = "<a href='%s'>%s" % (link, word)
      long_link_start.link = link
      return [long_link_start]

    match_object = WordProcessor.long_link_end_regexp.match(token)
    if match_object:
      word = cgi.escape(match_object.group(1))

      long_link_end = Token.CreateWithLineNo(LONG_LINK_END, token.line_no)
      long_link_end.value = token
      long_link_end.html = "%s</a>" % word
      return [long_link_end]

    match_object = WordProcessor.url_regexp.match(token)
    if match_object:
      url = Token.CreateWithLineNo(URL, token.line_no)
      url.value = token
      url.html = "<a href='%s'>%s</a>" % (token, token)
      url.link = token
      return [url]

    # Everything else is a normal word.
    word = Token.CreateWithLineNo(WORD, token.line_no)
    word.value = cgi.escape(token)
    word.html = word.value
    return [word]


def main():
  if len(sys.argv) == 1:
    input = sys.stdin.read()
  else:
    input = open(sys.argv[1]).read()

  try:
    token_list = tokenize(input)
  except Error:
    print('lexer failed.')
    sys.exit(1)

  for token in token_list:
    print(token)


if __name__ == '__main__':
  main()
