import itertools
import re

# ----------- AST Nodes -----------

'''
Shamus Herman - 2026
Logic Statement Truth Table Generator
This program takes a logical statement as input and generates its truth table.
'''

class Expr:
    def evaluate(self, context):
        raise NotImplementedError()
    
    def vars(self):
        raise NotImplementedError()
    
    def __str__(self):
        raise NotImplementedError()


class Var(Expr):
    def __init__(self, name):
        self.name = name
    
    def evaluate(self, context):
        return context[self.name]
    
    def vars(self):
        return {self.name}
    
    def __str__(self):
        return self.name


class Not(Expr):
    def __init__(self, operand):
        self.operand = operand
    
    def evaluate(self, context):
        return not self.operand.evaluate(context)
    
    def vars(self):
        return self.operand.vars()
    
    def __str__(self):
        return f"~{self.operand}"


class BinOp(Expr):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def vars(self):
        return self.left.vars().union(self.right.vars())


class And(BinOp):
    def evaluate(self, context):
        return self.left.evaluate(context) and self.right.evaluate(context)
    
    def __str__(self):
        return f"({self.left} & {self.right})"


class Or(BinOp):
    def evaluate(self, context):
        return self.left.evaluate(context) or self.right.evaluate(context)
    
    def __str__(self):
        return f"({self.left} | {self.right})"


class Implies(BinOp):
    def evaluate(self, context):
        return not self.left.evaluate(context) or self.right.evaluate(context)
    
    def __str__(self):
        return f"({self.left} -> {self.right})"


class Iff(BinOp):
    def evaluate(self, context):
        return self.left.evaluate(context) == self.right.evaluate(context)
    
    def __str__(self):
        return f"({self.left} <-> {self.right})"


# ----------- Tokenizer -----------

TOKEN_REGEX = r'\s*(~|&|\||->|<->|\(|\)|[A-Za-z][A-Za-z0-9_]*)\s*'

def tokenize(s):
    return re.findall(TOKEN_REGEX, s)


# ----------- Parser -----------

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def parse(self):
        return self.parse_iff()

    def parse_iff(self):
        left = self.parse_implies()
        while self.peek() == "<->":
            self.consume()
            right = self.parse_implies()
            left = Iff(left, right)
        return left

    def parse_implies(self):
        left = self.parse_or()
        while self.peek() == "->":
            self.consume()
            right = self.parse_or()
            left = Implies(left, right)
        return left

    def parse_or(self):
        left = self.parse_and()
        while self.peek() == "|":
            self.consume()
            right = self.parse_and()
            left = Or(left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.peek() == "&":
            self.consume()
            right = self.parse_not()
            left = And(left, right)
        return left

    def parse_not(self):
        if self.peek() == "~":
            self.consume()
            operand = self.parse_not()
            return Not(operand)
        else:
            return self.parse_atom()

    def parse_atom(self):
        tok = self.peek()
        if tok == "(":
            self.consume()
            expr = self.parse()
            if self.peek() != ")":
                raise ValueError("Expected closing parenthesis")
            self.consume()
            return expr
        else:
            self.consume()
            return Var(tok)


# ----------- Premise Sperator -------------------

def split_premises(statement):
    """
    Split a statement into premises and conclusion if 'therefore' is present. Using Commas and |- as well.
    Returns a tuple (premises_list, conclusion) or just premises_list if no conclusion.
    """

    parts = [] # Collected parts
    depth = 0 # Parenthesis depth
    start = 0 # Start index of current part
    i = 0

    while i < len(statement):
        char = statement[i] # Current character

        if char == '(':
            depth += 1
        elif char == ')':
            depth -= 1

        # Check for 'therefore' or '|-'
        
        if depth == 0:
            if statement.startswith('therefore', i):
                parts.append(statement[start:i].strip())
                conclusion = statement[i + len('therefore'):].strip()
                return parts, conclusion
            elif statement.startswith('|-', i):
                parts.append(statement[start:i].strip())
                conclusion = statement[i + len('|-'):].strip()
                return parts, conclusion
            elif char == ',':
                parts.append(statement[start:i].strip())
                start = i + 1

        i += 1

    tail = statement[start:].strip() # Remaining part after last split
    if tail:
        parts.append(tail)

    return parts 
        

# ----------- Sub-expression collector -----------

def collect_subexpressions(expr, collected=None):
    """
    Collect all unique non-variable sub-expressions in order from leaves to root.
    """
    if collected is None:
        collected = []

    # Skip if already collected
    if any(expr is node for node in collected):
        return collected

    # Recurse first
    if isinstance(expr, Not):
        collect_subexpressions(expr.operand, collected)
        collected.append(expr)
    elif isinstance(expr, BinOp):
        collect_subexpressions(expr.left, collected)
        collect_subexpressions(expr.right, collected)
        collected.append(expr)

    return collected

# ----------- Helpers -----------

def and_all(exprs):
    result = exprs[0]
    for e in exprs[1:]:
        result = And(result, e)
    return result


# ----------- Truth table generator -----------

def truth_table_multiple(exprs):
    # Collect all variables across all premises
    variables = sorted(set().union(*(e.vars() for e in exprs)))

    headers = variables + [str(e) for e in exprs] + ["ALL TRUE"]
    col_width = max(len(h) for h in headers) + 2

    header_line = " | ".join(h.center(col_width) for h in headers)
    print(header_line)
    print("-" * len(header_line))

    for values in itertools.product([False, True], repeat=len(variables)):
        env = dict(zip(variables, values))
        row = []

        # Variable columns
        for v in variables:
            row.append("T" if env[v] else "F")

        # Premise columns
        premise_vals = []
        for e in exprs:
            val = e.evaluate(env)
            premise_vals.append(val)
            row.append("T" if val else "F")

        # All-premises-true column
        row.append("T" if all(premise_vals) else "F")

        print(" | ".join(r.center(col_width) for r in row))



# ----------- Main -----------

if __name__ == "__main__":
    print("Logic Statement Truth Table Generator")
    print("Operators: ~ (NOT), & (AND), | (OR), -> (IMPLIES), <-> (IFF)")

    statement = input("Enter logic statement: ")

    split = split_premises(statement)

    # Multiple premises, no conclusion
    if isinstance(split, list):
        premises = []
        for p in split:
            tokens = tokenize(p)
            premises.append(Parser(tokens).parse())

        expr = and_all(premises)
        truth_table_multiple(premises)


    print( "Press R to run again or any other key to exit. ")

    if input().lower() == 'r':
        import os
        os.system('python ' + __file__)
    else:
        print("Exiting...")
        exit()

