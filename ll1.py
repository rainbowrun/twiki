#!/usr/bin/python3
#
# A strong-LL(1) parser.


class Error(Exception): pass


class Terminal(object): pass


class END_OF_INPUT(Terminal): pass


class PredictRule(object):
  def __init__(self):
    # Object instances for the matched right_hand_side.
    self.children = []

    # A dummy right hand side list. subclass should define this.
    self.right_hand_side_list = []


class Empty(PredictRule): pass


class Parser(object):
  """The LL1 Parser.

  Usage:
    parser = Parser(predict_rule_list)
    analysis_stack = parser.Parse(terminal_list)
  """

  def __init__(self, predict_rule_list):
    """Initialize the parser.

    Args:
      predict_rule_list: a list of class. Each class is a subclass of
          PredictRule.  The first element is the start predict rule.

    Raises:
      Error: when the grammar is not LL(1).
    """
    self.predict_rule_list = predict_rule_list

    # Set of Terminal and PredictRule types.
    self.terminal_type_set = set()
    self.predict_rule_type_set = set()
    self.ValidateRuleList_()

    # FIRST_set for all the predict rules.
    # Key is predict rule, value is a set of terminals plus Empty rule.
    self.FIRST_set = {}
    self.ComputeFirstSet_()

    # FOLLOW_set for all the predict rules.
    # Key is predict rule, value is a set of terminals.
    self.FOLLOW_set = {}
    self.ComputeFollowSet_()

    # Parse table.
    # Key is (PredictRule, terminal) and value is the right hand side.
    self.parse_table = {}
    self.GenerateParseTable_()

  def ValidateRuleList_(self):
    if len(self.predict_rule_list) == 0:
      raise Error("Empty grammar.")

    # Collect all the PredictRule.
    for predict_rule in self.predict_rule_list:
      if issubclass(predict_rule, PredictRule):
        self.predict_rule_type_set.add(predict_rule)
      else:
        raise Error("%s is not derived from PredictRule" % predict_rule)

    # Collect all the Terminal and verify all PredictRule appearing in the right
    # hand sides has a definition or every others are Terminal.
    for predict_rule in self.predict_rule_list:
      for right_hand_side in predict_rule.right_hand_side_list:
        for item in right_hand_side:
          if issubclass(item, PredictRule):
            if item not in self.predict_rule_type_set:
              raise Error("Undefined right hand side item: %s in "
                          "predict rule: %s." % (item,
                                                 predict_rule))
          elif issubclass(item, Terminal):
            self.terminal_type_set.add(item)
          else:
            raise Error("Right hand side item: %s in predict rule: %s is "
                        "neither PredictRule nor Terminal." % (item,
                                                               predict_rule))

  def PrintInternalTable(self):
    print('='*20, 'FIRST_set', '='*20)
    for predict_rule in self.predict_rule_list:
      print(predict_rule)
      print('\t', self.FIRST_set[predict_rule])
    print()

    print('='*20, 'FOLLOW_set', '='*20)
    for predict_rule in self.predict_rule_list:
      print(predict_rule)
      print('\t', self.FOLLOW_set[predict_rule])
    print()

    print('='*20, 'Parse table', '='*20)
    for (predict_rule, terminal), right_hand_side in self.parse_table.items():
      print('%s, %s ==> %s' % (predict_rule, terminal, right_hand_side))
    print()

  def AddToFirstSetOfRuleFromNthTermOfRightHandSide_(self, predict_rule,
                                                     right_hand_side, index):
    # If index is not an valid index, it means the right_hand_side is
    # either empty, or every item before position 'index' could derive Empty.
    # In any case, we should add Empty to FIRST_set since they both mean
    # predict_rule can derive Empty.
    if index == len(right_hand_side):
      self.FIRST_set[predict_rule].add(Empty)
      return

    item = right_hand_side[index]

    # If this is a terminal, add it.
    if issubclass(item, Terminal):
      self.FIRST_set[predict_rule].add(item)
      return

    # Now this is a predict rule, detect left recursive first.
    if item == predict_rule and index == 0:
      raise Error('Left recursive is not allowed. Found in %s.' % predict_rule)

    # Add every element in the FIRST_set of this predict rule.  If any element
    # is Empty, we need to consider next item in this right hand side.
    for element in self.FIRST_set[item]:
      if element == Empty:
        self.AddToFirstSetOfRuleFromNthTermOfRightHandSide_(
            predict_rule, right_hand_side, index+1)
      else:
        self.FIRST_set[predict_rule].add(element)

  def ComputeFirstSet_(self):
    # Initialize the FIRST_set to empty.
    for predict_rule in self.predict_rule_list:
      self.FIRST_set[predict_rule] = set()

    # Iterate to add Terminal or Empty to FIRST_set.
    old_count = 0
    while True:
      for predict_rule in self.predict_rule_list:
        for right_hand_side in predict_rule.right_hand_side_list:
          self.AddToFirstSetOfRuleFromNthTermOfRightHandSide_(
              predict_rule, right_hand_side, 0)

      new_count = sum([len(x) for x in self.FIRST_set.values()])
      if new_count != old_count:
        old_count = new_count
      else:
        break

  def GetFirstSetOfSententialForm_(self, right_hand_side, index):
    if index == len(right_hand_side):
      return set([Empty])

    item = right_hand_side[index]

    if issubclass(item, Terminal):
      return set([item])

    first_set = set()
    for element in self.FIRST_set[item]:
      if element == Empty:
        first_set |= self.GetFirstSetOfSententialForm_(right_hand_side, index+1)
      else:
        first_set.add(element)

    return first_set

  def MakeFollowSetFromRightHandSide_(self, A, right_hand_side):
    # Whenever a right-hand-side contains a non-terminal, such as A -> ...By, we
    # add all the terminals from FIRST_set(y) to FOLLOW_set(B), since these
    # terminals can follow B. In addition, if y derives Empty, we add all
    # terminals from FOLLOW_set(A) to FOLLOW_set(B).
    for index, B in enumerate(right_hand_side):
      if issubclass(B, Terminal):
        continue

      first_set = self.GetFirstSetOfSententialForm_(right_hand_side, index+1)
      for element in first_set:
        if element == Empty:
          self.FOLLOW_set[B] |= self.FOLLOW_set[A]

        else:
          self.FOLLOW_set[B].add(element)

  def ComputeFollowSet_(self):
    # Initialize the FOLLOW_set to empty.
    for predict_rule in self.predict_rule_list:
      self.FOLLOW_set[predict_rule] = set()

    # END_OF_INPUT is in FOLLOW_set of Start rule.
    self.FOLLOW_set[self.predict_rule_list[0]].add(END_OF_INPUT)

    # Iterate to add Terminal to FOLLOW_set.
    old_count = 0
    while True:
      for predict_rule in self.predict_rule_list:
        for right_hand_side in predict_rule.right_hand_side_list:
          self.MakeFollowSetFromRightHandSide_(predict_rule, right_hand_side)

      new_count = sum([len(x) for x in self.FOLLOW_set.values()])
      if new_count != old_count:
        old_count = new_count
      else:
        break

  def AddEntryToParseTable_(self, predict_rule, terminal, right_hand_side):
    # This parser is greedy, if it can make either an empty prediction or
    # another non-empty prediction, it will always favor the non-empty
    # prediction.
    #
    # In this case, an empty prediction and a non-empty prediction is not
    # regarded as a conflict.
    #
    # This greediness is necessary for any repeated structure which requires at
    # least one element, for example:
    #     A = a | a A
    # is natual for this situation but it is not LL(1).
    #     A = a A | epsilon
    # is LL(1) but it does not require at least one 'a'.
    # So we fall back to
    #     A = a A-follow
    #     A-follow = a A-follow | epsilon
    # and this last form is ambiguous without greedy rule.
    if (predict_rule, terminal) not in self.parse_table:
      self.parse_table[(predict_rule, terminal)] = right_hand_side
    elif self.parse_table[(predict_rule, terminal)] == right_hand_side:
      self.parse_table[(predict_rule, terminal)] = right_hand_side
    elif self.parse_table[(predict_rule, terminal)] == []:
      self.parse_table[(predict_rule, terminal)] = right_hand_side
    elif right_hand_side == []:
      pass
    else:
      raise Error(
          "Synxtax is not LL(1), (Predict rule: %s, Terminal: %s) has two "
          "conflict rules:\n\t%s\n\t%s\n" % (
              predict_rule,
              terminal,
              right_hand_side,
              self.parse_table[(predict_rule, terminal)]))

  def GenerateParseTable_(self):
    # To generate the parse table, for each right-hand-side like A -> alpha, we
    # add this right-hand-side to the [A, a] entry of the parse table for all
    # the terminal symbol 'a' in FIRST(alpha). BTW, if FIRST(alpha) contains
    # Empty, we also add alpha to [A, b] entry of the parse table for all the
    # terminal symbol 'b' in FOLLOW_set(A).
    for A in self.predict_rule_list:
      for alpha in A.right_hand_side_list:
        for a in self.GetFirstSetOfSententialForm_(alpha, 0):
          if a != Empty:
            self.AddEntryToParseTable_(A, a, alpha)
          else:
            for b in self.FOLLOW_set[A]:
              self.AddEntryToParseTable_(A, b, alpha)

  def ValidateTerminalList_(self, terminal_list):
    for terminal in terminal_list:
      if terminal.__class__ not in self.terminal_type_set:
        raise Error("The type of terminal %s is not defined in grammar." %
                    terminal)

    terminal_list.append(END_OF_INPUT())

  def Parse(self, terminal_list):
    """Parse the terminal list.

    Args:
      terminal_list: a list of terminal. Each termianl is an instance of
          subclass of Terminal.

    Returns:
      The analysis stack if parsing is successful.

    Raises:
      Error: when parsing fails.
    """
    self.ValidateTerminalList_(terminal_list)

    # analysis_stack stores the first item first, but predict_stack stores
    # the first item last. Python list does not support efficient operations
    # from the head of the list.
    predict_stack = [END_OF_INPUT(), self.predict_rule_list[0]()]
    analysis_stack = []

    terminal_index = 0
    terminal = terminal_list[terminal_index]
    while True:
      item = predict_stack.pop()

      # Match a terminal.
      if isinstance(item, Terminal):
        if terminal.__class__ == item.__class__:
          if terminal.__class__ == END_OF_INPUT:
            assert len(predict_stack) == 0
            assert terminal_index == len(terminal_list) - 1
            break

          item.parent.children[item.children_index] = terminal
          analysis_stack.append(terminal)
          terminal_index += 1
          assert terminal_index < len(terminal_list)
          terminal = terminal_list[terminal_index]
        else:
          raise Error("Fail to parse at terminal: %s" % terminal)

      # Match a predict rule.
      elif isinstance(item, PredictRule):
        try:
          right_hand_side = self.parse_table[(item.__class__,
                                              terminal.__class__)]
          assert len(item.children) == 0
          for index, child_type in enumerate(right_hand_side):
            child = child_type()
            child.parent = item
            child.children_index = index
            item.children.append(child)

          predict_stack.extend(reversed(item.children))
          analysis_stack.append(item)
        except KeyError:
          raise Error("Fail to parse at terminal: %s" % terminal)
      else:
        assert False, ("Invalid item in predict_stack, neither a Terminal "
                       "nor a PredictRule, %s" % item)

    return analysis_stack


if __name__ == '__main__':
  pass
