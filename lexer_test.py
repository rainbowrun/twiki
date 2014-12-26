#!/usr/bin/python3
#
# Test routines for lexer. To run this test. In the top-level directory, run
# python -m twiki.lexer_test

import textwrap

import lexer

token_list = lexer.tokenize('<verbatim>\ncode\n</verbatim>\n')
if not(len(token_list) == 2 and
       type(token_list[0]) == lexer.VERBATIM and
       type(token_list[1]) == lexer.NEW_LINE):
  raise Exception(token_list)

token_list = lexer.tokenize(textwrap.dedent("""\
    ---+abc
    ---++ abc
    ---+++ abc
    ---++++ abc
    ---+++++ abc
    ---++++++ abc
       * abc
          * abc
             * abc
                * abc
       1 abc
          1 abc
             1 abc
                1 abc
       # abc
          # abc
             # abc
                # abc
      abc
    \tabc
    """))
if not(len(token_list) == 60 and
       type(token_list[0]) == lexer.TITLE_LEAD1 and
       type(token_list[1]) == lexer.WORD and
       type(token_list[2]) == lexer.NEW_LINE and
       type(token_list[3]) == lexer.TITLE_LEAD2 and
       type(token_list[4]) == lexer.WORD and
       type(token_list[5]) == lexer.NEW_LINE and
       type(token_list[6]) == lexer.TITLE_LEAD3 and
       type(token_list[7]) == lexer.WORD and
       type(token_list[8]) == lexer.NEW_LINE and
       type(token_list[9]) == lexer.TITLE_LEAD4 and
       type(token_list[10]) == lexer.WORD and
       type(token_list[11]) == lexer.NEW_LINE and
       type(token_list[12]) == lexer.TITLE_LEAD5 and
       type(token_list[13]) == lexer.WORD and
       type(token_list[14]) == lexer.NEW_LINE and
       type(token_list[15]) == lexer.TITLE_LEAD6 and
       type(token_list[16]) == lexer.WORD and
       type(token_list[17]) == lexer.NEW_LINE and
       type(token_list[18]) == lexer.UNORDERED_LIST_LEAD1 and
       type(token_list[19]) == lexer.WORD and
       type(token_list[20]) == lexer.NEW_LINE and
       type(token_list[21]) == lexer.UNORDERED_LIST_LEAD2 and
       type(token_list[22]) == lexer.WORD and
       type(token_list[23]) == lexer.NEW_LINE and
       type(token_list[24]) == lexer.UNORDERED_LIST_LEAD3 and
       type(token_list[25]) == lexer.WORD and
       type(token_list[26]) == lexer.NEW_LINE and
       type(token_list[27]) == lexer.UNORDERED_LIST_LEAD4 and
       type(token_list[28]) == lexer.WORD and
       type(token_list[29]) == lexer.NEW_LINE and
       type(token_list[30]) == lexer.ORDERED_LIST_LEAD1 and
       type(token_list[31]) == lexer.WORD and
       type(token_list[32]) == lexer.NEW_LINE and
       type(token_list[33]) == lexer.ORDERED_LIST_LEAD2 and
       type(token_list[34]) == lexer.WORD and
       type(token_list[35]) == lexer.NEW_LINE and
       type(token_list[36]) == lexer.ORDERED_LIST_LEAD3 and
       type(token_list[37]) == lexer.WORD and
       type(token_list[38]) == lexer.NEW_LINE and
       type(token_list[39]) == lexer.ORDERED_LIST_LEAD4 and
       type(token_list[40]) == lexer.WORD and
       type(token_list[41]) == lexer.NEW_LINE and
       type(token_list[42]) == lexer.ORDERED_LIST_LEAD1 and
       type(token_list[43]) == lexer.WORD and
       type(token_list[44]) == lexer.NEW_LINE and
       type(token_list[45]) == lexer.ORDERED_LIST_LEAD2 and
       type(token_list[46]) == lexer.WORD and
       type(token_list[47]) == lexer.NEW_LINE and
       type(token_list[48]) == lexer.ORDERED_LIST_LEAD3 and
       type(token_list[49]) == lexer.WORD and
       type(token_list[50]) == lexer.NEW_LINE and
       type(token_list[51]) == lexer.ORDERED_LIST_LEAD4 and
       type(token_list[52]) == lexer.WORD and
       type(token_list[53]) == lexer.NEW_LINE and
       type(token_list[54]) == lexer.LINE_LEAD_WHITESPACE and
       type(token_list[55]) == lexer.WORD and
       type(token_list[56]) == lexer.NEW_LINE and
       type(token_list[57]) == lexer.LINE_LEAD_WHITESPACE and
       type(token_list[58]) == lexer.WORD and
       type(token_list[59]) == lexer.NEW_LINE):
  raise Exception(token_list)

token_list = lexer.tokenize(textwrap.dedent("""\
    %RED% %BLUE% %GREEN% %ENDCOLOR% %TOC%
    """))
if not(len(token_list) == 6 and
       type(token_list[0]) == lexer.COLOR_START and
       type(token_list[1]) == lexer.COLOR_START and
       type(token_list[2]) == lexer.COLOR_START and
       type(token_list[3]) == lexer.ENDCOLOR and
       type(token_list[4]) == lexer.TOC and
       type(token_list[5]) == lexer.NEW_LINE):
  raise Exception(token_list)

token_list = lexer.tokenize(textwrap.dedent("""\
    abc def hij
    *abc* *a b c*
    =abc= =a b c=
    _abc_ _a b c_
    abc? abc. abc! abc, abc: abc;
    """))
if not(len(token_list) == 32 and
       type(token_list[0]) == lexer.WORD and
       type(token_list[1]) == lexer.WORD and
       type(token_list[2]) == lexer.WORD and
       type(token_list[3]) == lexer.NEW_LINE and
       type(token_list[4]) == lexer.BOLD_WORD and
       type(token_list[5]) == lexer.BOLD_START_WORD and
       type(token_list[6]) == lexer.WORD and
       type(token_list[7]) == lexer.BOLD_END_WORD and
       type(token_list[8]) == lexer.NEW_LINE and
       type(token_list[9]) == lexer.FIXED_WIDTH_WORD and
       type(token_list[10]) == lexer.FIXED_WIDTH_START_WORD and
       type(token_list[11]) == lexer.WORD and
       type(token_list[12]) == lexer.FIXED_WIDTH_END_WORD and
       type(token_list[13]) == lexer.NEW_LINE and
       type(token_list[14]) == lexer.ITALICS_WORD and
       type(token_list[15]) == lexer.ITALICS_START_WORD and
       type(token_list[16]) == lexer.WORD and
       type(token_list[17]) == lexer.ITALICS_END_WORD and
       type(token_list[18]) == lexer.NEW_LINE and
       type(token_list[19]) == lexer.WORD and
       type(token_list[20]) == lexer.PUNCTURE and
       type(token_list[21]) == lexer.WORD and
       type(token_list[22]) == lexer.PUNCTURE and
       type(token_list[23]) == lexer.WORD and
       type(token_list[24]) == lexer.PUNCTURE and
       type(token_list[25]) == lexer.WORD and
       type(token_list[26]) == lexer.PUNCTURE and
       type(token_list[27]) == lexer.WORD and
       type(token_list[28]) == lexer.PUNCTURE and
       type(token_list[29]) == lexer.WORD and
       type(token_list[30]) == lexer.PUNCTURE and
       type(token_list[31]) == lexer.NEW_LINE):
  raise Exception(token_list)

token_list = lexer.tokenize(textwrap.dedent("""\
    [[WikiWord]] [[Link][WikiWord]]
    [[Link][WikiFirstWord SecondWord ThirdWord]]
    [[ImageLink][%IMAGE%]]
    [[ImageLink][%IMAGE:height=800:width=600%]]
    """))
if not(len(token_list) == 11 and
       type(token_list[0]) == lexer.SHORT_LINK and
       type(token_list[1]) == lexer.LONG_LINK and
       type(token_list[2]) == lexer.NEW_LINE and
       type(token_list[3]) == lexer.LONG_LINK_START and
       type(token_list[4]) == lexer.WORD and
       type(token_list[5]) == lexer.LONG_LINK_END and
       type(token_list[6]) == lexer.NEW_LINE and
       type(token_list[7]) == lexer.IMAGE_LINK and
       type(token_list[8]) == lexer.NEW_LINE and
       type(token_list[9]) == lexer.IMAGE_LINK and
       type(token_list[10]) == lexer.NEW_LINE):
  raise Exception(token_list)

token_list = lexer.tokenize(textwrap.dedent("""\
    http://www.google.com https://www.google.com
    mailto://www.google.com ftp://www.google.com
    """))
if not(len(token_list) == 6 and
       type(token_list[0]) == lexer.URL and
       type(token_list[1]) == lexer.URL and
       type(token_list[2]) == lexer.NEW_LINE and
       type(token_list[3]) == lexer.URL and
       type(token_list[4]) == lexer.URL and
       type(token_list[5]) == lexer.NEW_LINE):
  raise Exception(token_list)
