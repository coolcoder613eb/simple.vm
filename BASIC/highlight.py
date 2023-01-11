import sys
import os
from lex import *
from functools import partial


def fg(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def bg(r, g, b):
    return f"\033[48;2;{r};{g};{b}m"


reset = '\033[0m'
r = '\033[0m'
r = fg(0, 0, 0) + bg(255, 255, 255)

comments = fg(221, 0, 0)
strings = fg(0, 170, 0)
kws = fg(255, 119, 0)


# Parser object keeps track of current token and checks if the code matches the grammar.
class Parser:
    def __init__(self, lexer):
        self.lexer = lexer

        self.symbols = set()  # All variables we have declared so far.
        self.labelsDeclared = set()  # Keep track of all labels declared
        self.labelsGotoed = set()  # All labels goto'ed, so we know if they exist or not.

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken()  # Call this twice to initialize current and peek.

    # Return true if the current token matches.
    def checkToken(self, kind):
        return kind == self.curToken.kind

    # Return true if the next token matches.
    def checkPeek(self, kind):
        return kind == self.peekToken.kind

    # Try to match current token. If not, error. Advances the current token.
    def match(self, kind):
        if not self.checkToken(kind):
            self.abort("Expected " + kind.name + ", got " + self.curToken.kind.name)
        self.nextToken()

    # Advances the current token.
    def nextToken(self):
        self.curToken = self.peekToken
        self.peekToken = self.lexer.getToken()
        # No need to worry about passing the EOF, lexer handles that.

    def abort(self, message):
        sys.exit("Error. " + message)

    # Production rules.

    # program ::= {statement}
    def program(self):
        # self.emitter.headerLine("#include <stdio.h>")
        # self.emitter.headerLine("int main(void){")

        # Since some newlines are required in our grammar, need to skip the excess.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

        # Parse all the statements in the program.
        while not self.checkToken(TokenType.EOF):
            self.statement()

        print(r, end='')
        # Wrap things up.
        # self.emitter.emitLine("return 0;")
        # self.emitter.emitLine("}")

        # Check that each label referenced in a GOTO is declared.
        for label in self.labelsGotoed:
            if label not in self.labelsDeclared:
                self.abort("Attempting to GOTO to undeclared label: " + label)

    # One of the following statements...
    def statement(self):
        # Check the first token to see what kind of statement this is.

        # "REM"
        if self.checkToken(TokenType.REM):
            comment_text = 'REM '
            comment_words = []
            while not self.checkToken(TokenType.NEWLINE):
                self.nextToken()
                comment_words.append(self.curToken.text)
            comment_text += ' '.join(comment_words)
            print(comments + comment_text + r)
            # self.emitter.emitLine(comment_text)

        # "PRINT" (expression | string)
        if self.checkToken(TokenType.PRINT):
            self.nextToken()
            print(kws + 'PRINT ' + r, end='')
            if self.checkToken(TokenType.STRING):
                # Simple string, so print it.
                print(strings + '"' + self.curToken.text + '"' + r, end='')
                # self.emitter.emitLine("printf(\"" + self.curToken.text + "\\n\");")
                self.nextToken()

            else:
                # Expect an expression and print the result as a float.
                # self.emitter.emit("printf(\"%" + ".2f\\n\", (float)(")
                self.expression()
                # self.emitter.emitLine("));")

        # "IF" comparison "THEN" block "ENDIF"
        elif self.checkToken(TokenType.IF):
            self.nextToken()
            # self.emitter.emit("if(")
            print(kws + 'IF ' + r, end='')
            self.comparison()

            self.match(TokenType.THEN)
            print(kws + 'THEN ' + r, end='')
            self.nl()
            # self.emitter.emitLine("){")

            # Zero or more statements in the body.
            while not self.checkToken(TokenType.ENDIF):
                self.statement()

            print(kws + 'ENDIF ' + r, end='')
            self.match(TokenType.ENDIF)
            self.emitter.emitLine("}")

        # "WHILE" comparison "REPEAT" block "ENDWHILE"
        elif self.checkToken(TokenType.WHILE):
            self.nextToken()
            print(kws + 'WHILE ' + r, end='')
            # self.emitter.emit("while(")
            self.comparison()

            self.match(TokenType.REPEAT)
            print(kws + 'REPEAT ' + r, end='')
            self.nl()
            # self.emitter.emitLine("){")

            # Zero or more statements in the loop body.
            while not self.checkToken(TokenType.ENDWHILE):
                self.statement()

            self.match(TokenType.ENDWHILE)
            print(kws + 'ENDWHILE ' + r, end='')
            # self.emitter.emitLine("}")
        # "LABEL" ident
        elif self.checkToken(TokenType.LABEL):
            self.nextToken()
            print(kws + 'LABEL ' + r, end='')

            # Make sure this label doesn't already exist.
            if self.curToken.text in self.labelsDeclared:
                self.abort("Label already exists: " + self.curToken.text)
            self.labelsDeclared.add(self.curToken.text)

            # self.emitter.emitLine(self.curToken.text + ":")
            self.match(TokenType.IDENT)
            print(self.curToken.text + ' ', end='')

        # "GOTO" ident
        elif self.checkToken(TokenType.GOTO):
            self.nextToken()
            print(kws + 'GOTO ' + r, end='')
            self.labelsGotoed.add(self.curToken.text)
            # self.emitter.emitLine("goto " + self.curToken.text + ";")
            self.match(TokenType.IDENT)
            print(self.curToken.text + ' ', end='')

        # "LET" ident = expression
        elif self.checkToken(TokenType.LET):
            self.nextToken()
            print(kws + 'LET ' + r, end='')

            #  Check if ident exists in symbol table. If not, declare it.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                # self.emitter.headerLine("float " + self.curToken.text + ";")
                # print(self.curToken.text + ' ', end='')

            # self.emitter.emit(self.curToken.text + " = ")
            print(self.curToken.text + ' ', end='')
            self.match(TokenType.IDENT)

            print(self.curToken.text + ' ', end='')
            self.match(TokenType.EQ)

            self.expression()
            # self.emitter.emitLine(";")

        # "INPUT" ident
        elif self.checkToken(TokenType.INPUT):
            self.nextToken()
            print(kws + 'INPUT ' + r, end='')

            # If variable doesn't already exist, declare it.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                # self.emitter.headerLine("float " + self.curToken.text + ";")

            # Emit scanf but also validate the input. If invalid, set the variable to 0 and clear the input.
            # self.emitter.emitLine("if(0 == scanf(\"%" + "f\", &" + self.curToken.text + ")) {")
            # self.emitter.emitLine(self.curToken.text + " = 0;")
            # self.emitter.emit("scanf(\"%")
            # self.emitter.emitLine("*s\");")
            # self.emitter.emitLine("}")
            print(self.curToken.text + ' ', end='')
            self.match(TokenType.IDENT)
            

        # Newline.
        self.nl()

    # nl ::= '\n'+
    def nl(self):
        print("")
        # print(' ',end='')

        # Require at least one newline.
        self.match(TokenType.NEWLINE)
        # But we will allow extra newlines too, of course.
        while self.checkToken(TokenType.NEWLINE):
            print("")
            self.nextToken()

    # comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+
    def comparison(self):
        self.expression()
        # Must be at least one comparison operator and another expression.
        if self.isComparisonOperator():
            # self.emitter.emit(self.curToken.text)
            print(self.curToken.text + ' ', end='')
            self.nextToken()
            self.expression()
        # Can have 0 or more comparison operator and expressions.
        while self.isComparisonOperator():
            # self.emitter.emit(self.curToken.text)
            print(self.curToken.text + ' ', end='')
            self.nextToken()
            self.expression()

    # Return true if the current token is a comparison operator.
    def isComparisonOperator(self):
        return self.checkToken(TokenType.GT) or self.checkToken(TokenType.GTEQ) or self.checkToken(
            TokenType.LT) or self.checkToken(TokenType.LTEQ) or self.checkToken(TokenType.EQEQ) or self.checkToken(
            TokenType.NOTEQ)

    # expression ::= term {( "-" | "+" ) term}
    def expression(self):
        self.term()
        # Can have 0 or more +/- and expressions.
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            # self.emitter.emit(self.curToken.text)
            print(self.curToken.text + ' ', end='')
            self.nextToken()
            self.term()

    # term ::= unary {( "/" | "*" ) unary}
    def term(self):
        self.unary()
        # Can have 0 or more *// and expressions.
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            # self.emitter.emit(self.curToken.text)
            print(self.curToken.text + ' ', end='')
            self.nextToken()
            self.unary()

    # unary ::= ["+" | "-"] primary
    def unary(self):
        # Optional unary +/-
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            # self.emitter.emit(self.curToken.text)
            print(self.curToken.text + ' ', end='')
            self.nextToken()
        self.primary()

    # primary ::= number | ident
    def primary(self):
        if self.checkToken(TokenType.NUMBER):
            # self.emitter.emit(self.curToken.text)
            print(self.curToken.text + ' ', end='')
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            # Ensure the variable already exists.
            if self.curToken.text not in self.symbols:
                self.abort("Referencing variable before assignment: " + self.curToken.text)

            # self.emitter.emit(self.curToken.text)
            print(self.curToken.text + ' ', end='')
            self.nextToken()
        else:
            # Error!
            self.abort("Unexpected token at " + self.curToken.text)


def main():
    global print

    if len(sys.argv) < 2:
        sys.exit("Error: highlighter needs source file as argument.")
    with open(sys.argv[1], 'r') as inputFile:
        input = inputFile.read()

    # if '-s' in sys.argv or '--save' in sys.argv:
    #    out = '.'.join(sys.argv[1].split('.')[0:-1])+'.tiny.h'
    #    oldstdout = sys.stdout
    #    sys.stdout = open(out,'w',encoding='utf-8')

    print(r)
    oldprint = print
    print = partial(oldprint, end='\n  ')
    print('')

    # Initialize the lexer, emitter, and parser.
    lexer = Lexer(input)
    # emitter = Emitter(out)
    parser = Parser(lexer)

    parser.program()  # Start the parser.
    # emitter.writeFile() # Write the output to file.
    print = oldprint
    print(reset)


main()
