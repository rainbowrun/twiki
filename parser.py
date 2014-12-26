#!/usr/bin/python3
#
# LL(1) syntax for twiki.
#
# Usage:
#    parser = TwikiParser()
#    parser.Parser(string)

import sys

from . import ll1
from . import lexer


class PredictRule(ll1.PredictRule):
  """ Base class for all the predict rules.

  Providing basic implemention for HTML generation.
  """
  def __init__(self):
    ll1.PredictRule.__init__(self)
    self.html = ''

  # This method can be overridden by subclass.
  def GenerateHtml(self):
    self.html = "".join([child.html for child in self.children])

  def Generate(self):
    self.GenerateHtml()

    # Delete children's 'html' to save memory.
    # Delete the children does not help since they are still referenced in the
    # analysis stack.
    for child in self.children:
      del child.html


class WhitespaceJoinChildrenRule(PredictRule):
  def GenerateHtml(self):
    self.html = " ".join([child.html for child in self.children])


class plain_word(PredictRule): pass
plain_word.right_hand_side_list = [
    [lexer.WORD],
    [lexer.PUNCTURE],
    [lexer.COLOR_START],
    [lexer.ENDCOLOR],
    ]

class plain_word_list(WhitespaceJoinChildrenRule): pass
plain_word_list.right_hand_side_list = [
    [plain_word, plain_word_list],
    [],
    ]

class bold_word(WhitespaceJoinChildrenRule):
  right_hand_side_list = [
      [
          lexer.BOLD_WORD,
      ],
      [
          lexer.BOLD_START_WORD,
          plain_word_list,
          lexer.BOLD_END_WORD
      ],
  ]

class italics_word(WhitespaceJoinChildrenRule):
  right_hand_side_list = [
      [
          lexer.ITALICS_WORD,
      ],
      [
          lexer.ITALICS_START_WORD,
          plain_word_list,
          lexer.ITALICS_END_WORD,
      ],
  ]

class fixed_width_word(WhitespaceJoinChildrenRule):
  right_hand_side_list = [
      [
          lexer.FIXED_WIDTH_WORD,
      ],
      [
          lexer.FIXED_WIDTH_START_WORD,
          plain_word_list,
          lexer.FIXED_WIDTH_END_WORD,
      ],
  ]

class long_link(WhitespaceJoinChildrenRule):
  right_hand_side_list = [
      [
          lexer.LONG_LINK,
      ],
      [
          lexer.LONG_LINK_START,
          plain_word_list,
          lexer.LONG_LINK_END,
      ],
  ]

class formatted_word(PredictRule):
  right_hand_side_list = [
      [plain_word],
      [bold_word],
      [italics_word],
      [fixed_width_word],
      [lexer.SHORT_LINK],
      [long_link],
      [lexer.URL],
      [lexer.IMAGE_LINK],
      ]

# TODO: Remove the whitespace before punctures.
class formatted_word_list(WhitespaceJoinChildrenRule): pass
formatted_word_list.right_hand_side_list = [
    [formatted_word, formatted_word_list],
    [],
    ]

class line(PredictRule):
  def GenerateHtml(self):
    # If line is empty, generate a paragraph. Notice that we put the ending mark
    # before the opening mark because we have another pair of <p></p> for the
    # whole paragraph.
    #
    # As a side effect, we will generate two <p></p><p></p> if a paragraph only
    # has an empty line, but we decide not to fix it since it makes the code
    # more complicated.
    if len(self.children) == 2 and self.children[0].html.strip() == "":
      self.html = "\n</p>\n<p>\n"
    elif len(self.children) == 3 and self.children[1].html.strip() == "":
      self.html = "\n</p>\n<p>\n"
    else:
      self.html = " ".join([child.html for child in self.children])

  right_hand_side_list = [
      [
          formatted_word_list,
          lexer.NEW_LINE,
      ],
      [
          lexer.LINE_LEAD_WHITESPACE,
          formatted_word_list,
          lexer.NEW_LINE,
      ],
  ]

class paragraph_follow(PredictRule): pass
paragraph_follow.right_hand_side_list = [
    [line, paragraph_follow],
    [],
    ]

class paragraph(PredictRule):
  def GenerateHtml(self):
    self.html = "<p>\n%s\n%s</p>\n" % (self.children[0].html,
                                       self.children[1].html)

  right_hand_side_list = [
      [line, paragraph_follow],
      ]

class TitleBase(PredictRule):
  # Since we need to generate an unique anchor id for each title in the TOC,
  # a class variable is used to track this.
  global_anchor_id = 0

  def __init__(self):
    PredictRule.__init__(self)
    self.anchor_id = TitleBase.global_anchor_id
    TitleBase.global_anchor_id += 1

  def GenerateHtml(self):
    # Find level from class name. This is a HACK.
    type_name = str(type(self))
    class_name_start = type_name.find('title')
    assert class_name_start != -1
    self.level = int(type_name[class_name_start+5:class_name_start+6])
    self.html = "<h%s><a name=%s>%s</a></h%s>\n" % (
        self.level,
        self.anchor_id,
        self.children[1].html,
        self.level)
    self.title_html = self.children[1].html

# Use exec to generate all the title classes since they are similar.
# It is boring to write them all down.
title_class_template = """\
class title%(level)s(TitleBase):
  right_hand_side_list = [
      [lexer.TITLE_LEAD%(level)s, line],
      ]
"""

title_summary_template = """\
class title(PredictRule):
  right_hand_side_list = [
      %s
      ]
"""

MAX_TITLE_LEVEL = 6
title_class_source_list = []
title_summary_class_source_list = []
for i in range(MAX_TITLE_LEVEL):
  title_class_source_list.append(title_class_template % {'level': i+1})
  title_summary_class_source_list.append('[title%s],' % (i+1))
exec('\n'.join(title_class_source_list))
exec(title_summary_template % '\n'.join(title_summary_class_source_list))


class toc(PredictRule):
  right_hand_side_list = [
      [lexer.TOC, lexer.NEW_LINE],
      ]


class ListItem(PredictRule):
  def GenerateHtml(self):
    self.html = "<li>%s</li>\n" % "".join(
        [child.html for child in self.children])


class ListBase(PredictRule):
  def GenerateHtml(self):
    type_name = str(type(self.children[0]))
    if type_name.find("unorder_level") != -1:
      self.html = "\n<ul>\n%s\n</ul>\n" % self.children[0].html
    elif type_name.find("order_level") != -1:
      self.html = "\n<ol>\n%s\n</ol>\n" % self.children[0].html
    else:
      raise Error("Unknown list type: %s" % type_name)


# The list in last level does not have next level list as follwup.
list_class_last_followup_template = """\
class level%(level)s_list_item_follow(PredictRule):
  def GenerateHtml(self):
    if len(self.children) == 0:
      self.html = ''
    elif isinstance(self.children[0], lexer.NEW_LINE):
      self.html = '<p/>' + self.children[1].html
    else:
      self.html = "".join([child.html for child in self.children])

level%(level)s_list_item_follow.right_hand_side_list = [
    [lexer.LINE_LEAD_WHITESPACE, line, level%(level)s_list_item_follow],
    [lexer.NEW_LINE, level%(level)s_list_item_follow],
    [],
    ]
"""

list_class_normal_followup_template = """\
class level%(level)s_list_item_follow(PredictRule):
  def GenerateHtml(self):
    if len(self.children) == 0:
      self.html = ''
    elif isinstance(self.children[0], lexer.NEW_LINE):
      self.html = '<p/>' + self.children[1].html
    else:
      self.html = "".join([child.html for child in self.children])

level%(level)s_list_item_follow.right_hand_side_list = [
    [lexer.LINE_LEAD_WHITESPACE, line, level%(level)s_list_item_follow],
    [lexer.NEW_LINE, level%(level)s_list_item_follow],
    [level%(next_level)s_list, level%(level)s_list_item_follow],
    [],
    ]
"""

list_class_template = """\
class unorder_level%(level)s_list_item(ListItem):
  right_hand_side_list = [
      [
          lexer.UNORDERED_LIST_LEAD%(level)s,
          line,
          level%(level)s_list_item_follow,
      ],
  ]

class unorder_level%(level)s_list_follow(PredictRule): pass
unorder_level%(level)s_list_follow.right_hand_side_list = [
    [unorder_level%(level)s_list_item, unorder_level%(level)s_list_follow],
    [],
    ]

class unorder_level%(level)s_list(PredictRule): pass
unorder_level%(level)s_list.right_hand_side_list = [
    [unorder_level%(level)s_list_item, unorder_level%(level)s_list_follow],
    ]

class order_level%(level)s_list_item(ListItem):
  right_hand_side_list = [
      [
          lexer.ORDERED_LIST_LEAD%(level)s,
          line,
          level%(level)s_list_item_follow,
      ],
  ]

class order_level%(level)s_list_follow(PredictRule): pass
order_level%(level)s_list_follow.right_hand_side_list = [
    [order_level%(level)s_list_item, order_level%(level)s_list_follow],
    [],
    ]

class order_level%(level)s_list(PredictRule): pass
order_level%(level)s_list.right_hand_side_list = [
    [order_level%(level)s_list_item, order_level%(level)s_list_follow],
    ]

class level%(level)s_list(ListBase): pass
level%(level)s_list.right_hand_side_list = [
    [unorder_level%(level)s_list],
    [order_level%(level)s_list],
    ]
"""

MAX_LIST_LEVEL = 4
list_class_source_list = []
for level in range(MAX_LIST_LEVEL, 0, -1):
  if level < MAX_LIST_LEVEL:
    list_class_source_list.append(
        (list_class_normal_followup_template + list_class_template) % {
            'level': level,
            'next_level': level+1})
  else:
    list_class_source_list.append(
        (list_class_last_followup_template + list_class_template) % {
            'level': level})
exec('\n'.join(list_class_source_list))


class text_block(PredictRule):
  right_hand_side_list = [
      [paragraph],
      [title],
      [lexer.VERBATIM],
      [toc],
      [level1_list],
      ]

class document(PredictRule): pass
document.right_hand_side_list = [
    [text_block, document],
    [],
    ]


class TwikiParser(object):
  def __init__(self):
    predict_rule_list = [document]
    for item in globals().values():
      if hasattr(item, 'right_hand_side_list') and item != document:
        predict_rule_list.append(item)

    self.parser = ll1.Parser(predict_rule_list)

  def Parse(self, source):
    self.analysis_stack = self.parser.Parse(lexer.tokenize(source))

    # Evaluate 'html' attribute of every node from bottom up.  Terminal has
    # already had their HTML attribute ready.
    for item in reversed(self.analysis_stack):
      if not isinstance(item, ll1.Terminal):
        item.Generate()

    self.generate_toc()

    return self.analysis_stack[0].html

  def generate_toc(self):
    toc_signature = '<toc/>'

    # 0, If we don't have TOC at all, quit.
    if self.analysis_stack[0].html.find(toc_signature) == -1:
      return

    # 1, Collect all the title rule into a list of 3 elements tuple of
    # (level, text, anchor_id).
    title_list = []
    for rule in self.analysis_stack:
      if isinstance(rule, TitleBase):
        # TODO(xiaopanzhang): If the title text is a link, try to extract text.
        title_list.append((
            rule.level,
            rule.title_html,
            rule.anchor_id))

    # 2, Generate the TOC as a HTML list.
    text_list = []
    current_level = 0
    for level, text, anchor_id in title_list:
      # Adjust list level.
      if level > current_level:
        for i in range(level - current_level):
          text_list.append('<ul>')
        current_level = level
      elif level < current_level:
        for i in range(current_level - level):
          text_list.append('</ul>')
        current_level = level

      # Output the text.
      text_list.append('<li><a href="#%s">' % anchor_id)
      text_list.append(text)
      text_list.append('</a></li>')

    # Close list level.
    for i in range(current_level):
      text_list.append('</ul>')

    # 3. Replace the TOC signature of the generated HTML in root node.
    #    Unfortunately, my algorithm can't handle the sequence of generating
    #    TOC and html.
    self.analysis_stack[0].html = self.analysis_stack[0].html.replace(
        toc_signature, '\n'.join(text_list))


def main():
  if len(sys.argv) == 1:
    input = sys.stdin.read()
  else:
    input = open(sys.argv[1]).read()

  print(TwikiParser().Parse(input))


if __name__ == '__main__':
  main()
