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


# ----------- Truth table generator -----------

def truth_table(expr):
    variables = sorted(expr.vars())
    subexprs = collect_subexpressions(expr)

    # Column headers
    headers = variables + [str(e) for e in subexprs]
    col_width = max(len(h) for h in headers) + 2
    header_line = " | ".join(h.center(col_width) for h in headers)
    print(header_line)
    print("-" * len(header_line))

    # Generate all truth assignments
    for values in itertools.product([False, True], repeat=len(variables)):
        env = dict(zip(variables, values))
        row = []

        # Variable values
        for var in variables:
            row.append("T" if env[var] else "F")

        # Sub-expression values
        for node in subexprs:
            row.append("T" if node.evaluate(env) else "F")

        # Print row
        print(" | ".join(r.center(col_width) for r in row))


# ----------- Main -----------

if __name__ == "__main__":
    print("Logic Statement Truth Table Generator")
    print("Operators: ~ (NOT), & (AND), | (OR), -> (IMPLIES), <-> (IFF)")
    statement = input("Enter logic statement: ")
    tokens = tokenize(statement)
    expr = Parser(tokens).parse()
    truth_table(expr)

    print("\nDone. Press R to run another statement.")
    print("Press Enter to exit.")
    if input().strip().lower() == 'r':
        import os
        os.system('python ' + __file__)  # Restart the script
    input()  # Wait for user to press Enter before exiting
