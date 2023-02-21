import sys
from lex import *

# Parser object keeps track of current token and checks if the code matches the grammar.
class Parser:
    def __init__(self, lexer, emitter):
        self.lexer = lexer
        self.emitter = emitter

        self.symbols = set()    # All variables we have declared so far.
        self.labelsDeclared = set() # Keep track of all labels declared
        self.labelsGotoed = set() # All labels goto'ed, so we know if they exist or not.
        self._l = 0

        self.varreg = 10
        self.thevars = {}

        self.curToken = None
        self.peekToken = None
        self.nextToken()
        self.nextToken()    # Call this twice to initialize current and peek.

    def l(self,do=True):
        l = self._l
        if do:
            self._l += 1
        return 'l'+str(l)

    # Return true if the current token matches.
    def checkToken(self, kind):
        return kind == self.curToken.kind

    # Return true if the next token matches.
    def checkPeek(self, kind):
        return kind == self.peekToken.kind

    # Try to match current token. If not, error. Advances the current token.
    def match(self, kind):
        if not self.checkToken(kind):
            self.abort("Expected " + kind.name + ", got " + self.curToken.kind.name+', at "'+self.curToken.text+'"')
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
        #self.emitter.headerLine("#include <stdio.h>")
        #self.emitter.headerLine("int main(void){")

        # Since some newlines are required in our grammar, need to skip the excess.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

        # Parse all the statements in the program.
        while not self.checkToken(TokenType.EOF):
            self.statement()

        # Wrap things up.
        #self.emitter.emitLine("return 0;")
        #self.emitter.emitLine("}")

        # Check that each label referenced in a GOTO is declared.
        for label in self.labelsGotoed:
            if label not in self.labelsDeclared:
                self.abort("Attempting to GOTO to undeclared label: " + label)

    # One of the following statements...
    def statement(self):
        # Check the first token to see what kind of statement this is.

        # "REM"
        if self.checkToken(TokenType.REM):
            comment_text = '; '
            comment_words = []
            while not self.checkToken(TokenType.NEWLINE):
                self.nextToken()
                comment_words.append(self.curToken.text)
            comment_text += ' '.join(comment_words)
            self.emitter.emitLine(comment_text)


        # "PRINT" (expression | string)
        if self.checkToken(TokenType.PRINT):
            self.nextToken()

            if self.checkToken(TokenType.STRING):
                # Simple string, so print it.
                self.emitter.emitLine("store #9, \"" + self.curToken.text + "\\n\"")
                self.emitter.emitLine("print_str #9")
                self.nextToken()
            elif self.checkToken(TokenType.IDENT):
                try:
                    self.emitter.emitLine(f'store #9, #{self.thevars[self.curToken.text]}')
                    #self.emitter.emitLine('int2string #9')
                    self.emitter.emitLine('store #2, "\\n"')
                    self.emitter.emitLine('concat #3, #9, #2')
                    self.emitter.emitLine('store #9, #3')
                    self.emitter.emitLine('print_str #9')
                except:
                    raise KeyError(f'{self.curToken.text} is not in {self.thevars.keys()}!')
                self.nextToken()
            else:
                # Expect an expression and print the result as a float. #######
                self.emitter.emit("printf(\"%" + ".2f\\n\", (float)(")
                self.expression()
                self.emitter.emitLine("));")

        # "IF" comparison "THEN" block "ENDIF"
        elif self.checkToken(TokenType.IF):
            self.nextToken()
            self.emitter.emit("if(")
            self.comparison()

            self.match(TokenType.THEN)
            self.nl()
            self.emitter.emitLine("){")

            # Zero or more statements in the body.
            while not self.checkToken(TokenType.ENDIF):
                self.statement()

            self.match(TokenType.ENDIF)
            self.emitter.emitLine("}")

        # "WHILE" comparison "REPEAT" block "ENDWHILE"
        elif self.checkToken(TokenType.WHILE):
            self.nextToken()
            self.emitter.emit("while(")
            self.comparison()

            self.match(TokenType.REPEAT)
            self.nl()
            self.emitter.emitLine("){")

            # Zero or more statements in the loop body.
            while not self.checkToken(TokenType.ENDWHILE):
                self.statement()

            self.match(TokenType.ENDWHILE)
            self.emitter.emitLine("}")
        # "LABEL" ident
        elif self.checkToken(TokenType.LABEL):
            self.nextToken()

            # Make sure this label doesn't already exist.
            if self.curToken.text in self.labelsDeclared:
                self.abort("Label already exists: " + self.curToken.text)
            self.labelsDeclared.add(self.curToken.text)

            self.emitter.emitLine( ":"+self.curToken.text)
            self.match(TokenType.IDENT)

        # "GOTO" ident
        elif self.checkToken(TokenType.GOTO):
            self.nextToken()
            self.labelsGotoed.add(self.curToken.text)
            self.emitter.emitLine("goto " + self.curToken.text)
            self.match(TokenType.IDENT)

        # "LET" ident = expression
        elif self.checkToken(TokenType.LET):
            self.nextToken()

            #  Check if ident exists in symbol table. If not, declare it.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                self.thevars.update({self.curToken.text: self.varreg})

                #self.emitter.headerLine("float " + self.curToken.text + ";")


            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)

            self.expression()
            self.emitter.emitLine(f"store #{self.varreg}, #8")
            self.varreg += 1
            #self.emitter.emitLine(";")

        # "INPUT" ident
        elif self.checkToken(TokenType.INPUT):
            self.nextToken()

            # If variable doesn't already exist, declare it.
            if self.curToken.text not in self.symbols:
                self.symbols.add(self.curToken.text)
                #self.emitter.headerLine("float " + self.curToken.text + ";")

            ########

            self.emitter.emitLine('in_str #9')
            #self.emitter.emitLine('string2int #9')
            try:
                self.emitter.emitLine(f'store #{self.thevars[self.curToken.text]}, #9')
            except:
                raise KeyError(f'{self.curToken.text} is not in {self.thevars.keys()}!')
            # Emit scanf but also validate the input. If invalid, set the variable to 0 and clear the input.
            #self.emitter.emitLine(self.l()+':')
            #self.emitter.emitLine(self.curToken.text + " = 0;")
            #self.emitter.emit("scanf(\"%")
            #self.emitter.emitLine("*s\");")
            #self.emitter.emitLine("}")
            self.match(TokenType.IDENT)

        # Newline.
        self.nl()

    # nl ::= '\n'+
    def nl(self):
        #print("NEWLINE")

        # Require at least one newline.
        self.match(TokenType.NEWLINE)
        # But we will allow extra newlines too, of course.
        while self.checkToken(TokenType.NEWLINE):
            self.nextToken()

    # comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+
    def comparison(self):
        self.expression()
        # Must be at least one comparison operator and another expression.
        if self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()
        # Can have 0 or more comparison operator and expressions.
        while self.isComparisonOperator():
            self.emitter.emit(self.curToken.text)
            self.nextToken()
            self.expression()

    # Return true if the current token is a comparison operator.
    def isComparisonOperator(self):
        return self.checkToken(TokenType.GT) or self.checkToken(TokenType.GTEQ) or self.checkToken(TokenType.LT) or self.checkToken(TokenType.LTEQ) or self.checkToken(TokenType.EQEQ) or self.checkToken(TokenType.NOTEQ)

    # expression ::= term {( "-" | "+" ) term}
    def expression(self):
        # reg 8
        self.term()
        # Can have 0 or more +/- and expressions.
        while self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            #self.emitter.emit(self.curToken.text)
            print(self.curToken.text)
            self.nextToken()
            self.term()


    # term ::= unary {( "/" | "*" ) unary}
    def term(self):
        self.unary()
        # Can have 0 or more *// and expressions.
        while self.checkToken(TokenType.ASTERISK) or self.checkToken(TokenType.SLASH):
            #self.emitter.emit(self.curToken.text)
            print(self.curToken.text)
            self.nextToken()
            self.unary()


    # unary ::= ["+" | "-"] primary
    def unary(self):
        # Optional unary +/-
        if self.checkToken(TokenType.PLUS) or self.checkToken(TokenType.MINUS):
            #self.emitter.emit(self.curToken.text)
            print(self.curToken.text)
            self.nextToken()
        self.primary()

    # primary ::= number | ident
    def primary(self):
        if self.checkToken(TokenType.NUMBER):
            self.emitter.emitLine(f'store #8, {self.curToken.text}')
            self.nextToken()
        if self.checkToken(TokenType.STRING):
            self.emitter.emitLine(f'store #8, \"{self.curToken.text}\\n\"')
            self.nextToken()
        elif self.checkToken(TokenType.IDENT):
            # Ensure the variable already exists.
            if self.curToken.text not in self.symbols:
                self.abort("Referencing variable before assignment: " + self.curToken.text)

            self.emitter.emitLine(f'store #8, #{self.thevars[self.curToken.text]}')
            self.nextToken()
        else:
            # Error!
            self.abort("Unexpected token at " + self.curToken.text)
