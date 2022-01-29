#! /usr/bin/python

# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from basictoken import BASICToken as Token
from flowsignal import FlowSignal
import math
import random
from time import monotonic


"""Implements a BASIC array, which may have up
to three dimensions of fixed size.

"""
class BASICArray:

    def __init__(self, dimensions):
        """Initialises the object with the specified
        number of dimensions. Maximum number of
        dimensions is three

        :param dimensions: List of array dimensions and their
        corresponding sizes

        """
        self.dims = min(3,len(dimensions))

        if self.dims == 0:
            raise SyntaxError("Zero dimensional array specified")

        # Check for invalid sizes and ensure int
        for i in range(self.dims):
            if dimensions[i] < 0:
                raise SyntaxError("Negative array size specified")
            # Allow sizes like 1.0f, but not 1.1f
            if int(dimensions[i]) != dimensions[i]:
                raise SyntaxError("Fractional array size specified")
            dimensions[i] = int(dimensions[i])

        # MSBASIC: Initialize to Zero
        # MSBASIC: Overdim by one, as some dialects are 1 based and expect
        #          to use the last item at index = size
        if self.dims == 1:
            self.data = [0 for x in range(dimensions[0] + 1)]
        elif self.dims == 2:
            self.data = [
                [0 for x in range(dimensions[1] + 1)] for x in range(dimensions[0] + 1)
            ]
        else:
            self.data = [
                [
                    [0 for x in range(dimensions[2] + 1)]
                    for x in range(dimensions[1] + 1)
                ]
                for x in range(dimensions[0] + 1)
            ]

    def pretty_print(self):
        print(str(self.data))

"""Implements a BASIC parser that parses a single
statement when supplied.

"""
class BASICParser:

    def __init__(self, basicdata):
        # Symbol table to hold variable names mapped
        # to values
        self.__symbol_table = {}

        # Stack on which to store operands
        # when evaluating expressions
        self.__operand_stack = []

        # BasicDATA structure containing program DATA Statements
        self.__data = basicdata
        # List to hold values read from DATA statements
        self.__data_values = []

        # These values will be
        # initialised on a per
        # statement basis
        self.__tokenlist = []
        self.__tokenindex = None

        # Previous flowsignal used to determine initializion of
        # loop variable
        self.last_flowsignal = None

        # Set to keep track of print column across multiple print statements
        self.__prnt_column = 0

        #file handle list
        self.__file_handles = {}

    def parse(self, tokenlist, line_number):
        """Must be initialised with the list of
        BTokens to be processed. These tokens
        represent a BASIC statement without
        its corresponding line number.

        :param tokenlist: The tokenized program statement
        :param line_number: The line number of the statement

        :return: The FlowSignal to indicate to the program
        how to branch if necessary, None otherwise

        """

        # Remember the line number to aid error reporting
        self.__line_number = line_number
        self.__tokenlist = []
        self.__tokenindex = 0
        linetokenindex = 0
        for token in tokenlist:
            # If statements will always be the last statement processed on a line so
            # any colons found after an IF are part of the condition execution statements
            # and will be processed in the recursive call to parse
            if token.category == token.IF:
                # process IF statement to move __tokenidex to the code block
                # of the THEN or ELSE and then call PARSE recursively to process that code block
                # this will terminate the token loop by RETURNing to the calling module
                #
                # **Warning** if an IF stmt is used in the THEN code block or multiple IF statement are used
                # in a THEN or ELSE block the block grouping is ambiguous and logical processing may not
                # function as expected. There is no ambiguity when single IF statements are placed within ELSE blocks
                linetokenindex += self.__tokenindex
                self.__tokenindex = 0
                self.__tokenlist = tokenlist[linetokenindex:]

                # Assign the first token
                self.__token = self.__tokenlist[0]
                flow = self.__stmt() # process IF statement
                if flow and (flow.ftype == FlowSignal.EXECUTE):
                    # recursive call to process THEN/ELSE block
                    try:
                        return self.parse(tokenlist[linetokenindex+self.__tokenindex:],line_number)
                    except RuntimeError as err:
                        raise RuntimeError(str(err)+' in line ' + str(self.__line_number))
                else:
                    # branch on original syntax 'IF cond THEN lineno [ELSE lineno]'
                    # in this syntax the then or else code block is not a legal basic statement
                    # so recursive processing can't be used
                    return flow
            elif token.category == token.COLON:
                # Found a COLON, process tokens found to this point
                linetokenindex += self.__tokenindex
                self.__tokenindex = 0

                # Assign the first token
                self.__token = self.__tokenlist[self.__tokenindex]

                flow = self.__stmt()
                if flow:
                    return flow

                linetokenindex += 1
                self.__tokenlist = []
            elif token.category == token.ELSE and self.__tokenlist[0].category != token.OPEN:
                # if we find an ELSE and we are not processing an OPEN statement, we must
                # be in a recursive call and be processing a THEN block
                # since we're processing the THEN block we are done if we hit an ELSE
                break
            else:
                self.__tokenlist.append(token)

        # reached end of statement, process tokens collected since last COLON (or from start if no COLONs)
        linetokenindex += self.__tokenindex
        self.__tokenindex = 0
        # Assign the first token
        self.__token = self.__tokenlist[self.__tokenindex]

        return self.__stmt()

    def __advance(self):
        """Advances to the next token

        """
        # Move to the next token
        self.__tokenindex += 1

        # Acquire the next token if there any left
        if not self.__tokenindex >= len(self.__tokenlist):
            self.__token = self.__tokenlist[self.__tokenindex]

    def __consume(self, expected_category):
        """Consumes a token from the list

        """
        if self.__token.category == expected_category:
            self.__advance()

        else:
            raise RuntimeError('Expecting ' + Token.catnames[expected_category] +
                               ' in line ' + str(self.__line_number))

    def __stmt(self):
        """Parses a program statement

        :return: The FlowSignal to indicate to the program
        how to branch if necessary, None otherwise

        """
        if self.__token.category in [Token.FOR, Token.IF, Token.NEXT,
                                     Token.ON]:
            return self.__compoundstmt()

        else:
            return self.__simplestmt()

    def __simplestmt(self):
        """Parses a non-compound program statement

        :return: The FlowSignal to indicate to the program
        how to branch if necessary, None otherwise

        """
        if self.__token.category == Token.NAME:
            self.__assignmentstmt()
            return None

        elif self.__token.category == Token.PRINT:
            self.__printstmt()
            return None

        elif self.__token.category == Token.LET:
            self.__letstmt()
            return None

        elif self.__token.category == Token.RETURN:
            return self.__returnstmt()

        elif self.__token.category == Token.STOP:
            return self.__stopstmt()

        elif self.__token.category == Token.INPUT:
            self.__inputstmt()
            return None

        elif self.__token.category == Token.DATA:
            self.__datastmt()
            return None

    def __printstmt(self):
        self.__advance()   # Advance past PRINT token

        fileIO = False
        if self.__token.category == Token.HASH:
            fileIO = True

            # Process the # keyword
            self.__consume(Token.HASH)

            # Acquire the file number
            self.__expr()
            filenum = self.__operand_stack.pop()

            if self.__file_handles.get(filenum) == None:
                raise RuntimeError("PRINT: file #"+str(filenum)+" not opened in line " + str(self.__line_number))

            # Process the comma
            if self.__tokenindex < len(self.__tokenlist) and self.__token.category != Token.COLON:
                self.__consume(Token.COMMA)

        # Check there are items to print
        if not self.__tokenindex >= len(self.__tokenlist):
            prntTab = (self.__token.category == Token.TAB)
            self.__logexpr()

            if prntTab:
                if self.__prnt_column >= len(self.__operand_stack[-1]):
                    if fileIO:
                        self.__file_handles[filenum].write("\n")
                    else:
                        print()
                    self.__prnt_column = 0

                current_pr_column = len(self.__operand_stack[-1]) - self.__prnt_column
                self.__prnt_column = len(self.__operand_stack.pop()) - 1
                if current_pr_column > 1:
                    if fileIO:
                        self.__file_handles[filenum].write(" "*(current_pr_column-1))
                    else:
                        print(" "*(current_pr_column-1), end="")
            else:
                self.__prnt_column += len(str(self.__operand_stack[-1]))
                if fileIO:
                    self.__file_handles[filenum].write('%s' %(self.__operand_stack.pop()))
                else:
                    print(self.__operand_stack.pop(), end='')

            while self.__token.category == Token.SEMICOLON:
                if self.__tokenindex == len(self.__tokenlist) - 1:
                    # If a semicolon ends this line, don't print
                    # a newline.. a-la ms-basic
                    self.__advance()
                    return
                self.__advance()
                prntTab = (self.__token.category == Token.TAB)
                self.__logexpr()

                if prntTab:
                    if self.__prnt_column >= len(self.__operand_stack[-1]):
                        if fileIO:
                            self.__file_handles[filenum].write("\n")
                        else:
                            print()
                        self.__prnt_column = 0
                    current_pr_column = len(self.__operand_stack[-1]) - self.__prnt_column
                    if fileIO:
                        self.__file_handles[filenum].write(" "*(current_pr_column-1))
                    else:
                        print(" "*(current_pr_column-1), end="")
                    self.__prnt_column = len(self.__operand_stack.pop()) - 1
                else:
                    self.__prnt_column += len(str(self.__operand_stack[-1]))
                    if fileIO:
                        self.__file_handles[filenum].write('%s' %(self.__operand_stack.pop()))
                    else:
                        print(self.__operand_stack.pop(), end='')

        # Final newline
        if fileIO:
            self.__file_handles[filenum].write("\n")
        else:
            print()
        self.__prnt_column = 0

    def __letstmt(self):
        """Parses a LET statement,
        consuming the LET keyword.
        """
        self.__advance()  # Advance past the LET token
        self.__assignmentstmt()

    def __gotostmt(self):
        """Parses a GOTO statement

        :return: A FlowSignal containing the target line number
        of the GOTO

        """
        self.__advance()  # Advance past GOTO token
        self.__expr()

        # Set up and return the flow signal
        return FlowSignal(ftarget=self.__operand_stack.pop())

    def __gosubstmt(self):
        """Parses a GOSUB statement

        :return: A FlowSignal containing the first line number
        of the subroutine

        """

        self.__advance()  # Advance past GOSUB token
        self.__expr()

        # Set up and return the flow signal
        return FlowSignal(ftarget=self.__operand_stack.pop(),
                          ftype=FlowSignal.GOSUB)

    def __returnstmt(self):
        """Parses a RETURN statement"""

        self.__advance()  # Advance past RETURN token

        # Set up and return the flow signal
        return FlowSignal(ftype=FlowSignal.RETURN)

    def __stopstmt(self):
        """Parses a STOP statement"""

        self.__advance()  # Advance past STOP token

        for handles in self.__file_handles:
            self.__file_handles[handles].close()
        self.__file_handles.clear()

        return FlowSignal(ftype=FlowSignal.STOP)

    def __assignmentstmt(self):
        """Parses an assignment statement,
        placing the corresponding
        variable and its value in the symbol
        table.

        """
        left = self.__token.lexeme  # Save lexeme of
                                    # the current token
        self.__advance()

        if self.__token.category == Token.LEFTPAREN:
            # We are assigning to an array
            self.__arrayassignmentstmt(left)

        else:
            # We are assigning to a simple variable
            self.__consume(Token.ASSIGNOP)
            self.__logexpr()

            # Check that we are using the right variable name format
            right = self.__operand_stack.pop()

            if left.endswith('$') and not isinstance(right, str):
                raise SyntaxError('Syntax error: Attempt to assign non string to string variable' +
                                  ' in line ' + str(self.__line_number))

            elif not left.endswith('$') and isinstance(right, str):
                raise SyntaxError('Syntax error: Attempt to assign string to numeric variable' +
                                  ' in line ' + str(self.__line_number))

            self.__symbol_table[left] = right

    def __dimstmt(self):
        """Parses  DIM statement and creates a symbol
        table entry for an array of the specified
        dimensions.

        """
        self.__advance()  # Advance past DIM keyword

        # MSBASIC: allow dims of multiple arrays delimited by commas
        while True:
            # Extract the array name, append a suffix so
            # that we can distinguish from simple variables
            # in the symbol table
            name = self.__token.lexeme + "_array"
            self.__advance()  # Advance past array name

            self.__consume(Token.LEFTPAREN)

            # Extract the dimensions
            dimensions = []
            if not self.__tokenindex >= len(self.__tokenlist):
                self.__expr()
                dimensions.append(self.__operand_stack.pop())

                while self.__token.category == Token.COMMA:
                    self.__advance()  # Advance past comma
                    self.__expr()
                    dimensions.append(self.__operand_stack.pop())

            self.__consume(Token.RIGHTPAREN)

            if len(dimensions) > 3:
                raise SyntaxError(
                    "Maximum number of array dimensions is three "
                    + "in line "
                    + str(self.__line_number)
                )

            self.__symbol_table[name] = BASICArray(dimensions)

            if self.__tokenindex == len(self.__tokenlist):
                # We have parsed the last token here...
                return
            else:
                self.__consume(Token.COMMA)

    def __expr(self):

        self.__term()   

        while self.__token.category in [Token.PLUS, Token.MINUS]:
            savedcategory = self.__token.category
            self.__advance()
            self.__term() 
                 
            rightoperand = self.__operand_stack.pop()
            leftoperand = self.__operand_stack.pop()

            if savedcategory == Token.PLUS:
                self.__operand_stack.append(leftoperand + rightoperand)

            else:
                self.__operand_stack.append(leftoperand - rightoperand)

    def __term(self):
        self.__sign = 1  
                     
        self.__factor()  

        while self.__token.category in [Token.TIMES, Token.DIVIDE, Token.MODULO]:
            savedcategory = self.__token.category
            self.__advance()
            self.__sign = 1  
            self.__factor()  
            rightoperand = self.__operand_stack.pop()
            leftoperand = self.__operand_stack.pop()

            if savedcategory == Token.TIMES:
                self.__operand_stack.append(leftoperand * rightoperand)

            elif savedcategory == Token.DIVIDE:
                self.__operand_stack.append(leftoperand / rightoperand)

            else:
                self.__operand_stack.append(leftoperand % rightoperand)

    def __factor(self):
        if self.__token.category == Token.PLUS:
            self.__advance()
            self.__factor()

        elif self.__token.category == Token.MINUS:
            self.__sign = -self.__sign
            self.__advance()
            self.__factor()

        elif self.__token.category == Token.UNSIGNEDINT:
            self.__operand_stack.append(self.__sign*int(self.__token.lexeme))
            self.__advance()

        elif self.__token.category == Token.UNSIGNEDFLOAT:
            self.__operand_stack.append(self.__sign*float(self.__token.lexeme))
            self.__advance()

        elif self.__token.category == Token.STRING:
            self.__operand_stack.append(self.__token.lexeme)
            self.__advance()

        elif self.__token.category == Token.LEFTPAREN:
            self.__advance()

            # Save sign because expr() calls term() which resets
            # sign to 1
            savesign = self.__sign
            self.__logexpr()  # Value of expr is pushed onto stack

            if savesign == -1:
                # Change sign of expression
                self.__operand_stack[-1] = -self.__operand_stack[-1]

            self.__consume(Token.RIGHTPAREN)

        elif self.__token.category in Token.functions:
            self.__operand_stack.append(self.__evaluate_function(self.__token.category))

        else:
            raise RuntimeError('Expecting factor in numeric expression' +
                               ' in line ' + str(self.__line_number) +
                               self.__token.lexeme)

    def __compoundstmt(self):
        if self.__token.category == Token.FOR:
            return self.__forstmt()

        elif self.__token.category == Token.NEXT:
            return self.__nextstmt()

        elif self.__token.category == Token.IF:
            return self.__ifstmt()

        elif self.__token.category == Token.ON:
            return self.__ongosubstmt()

    def __ifstmt(self):
        self.__advance()  
        self.__logexpr()

 
        saveval = self.__operand_stack.pop()

        self.__consume(Token.THEN)

        if self.__token.category != Token.UNSIGNEDINT:
            if saveval:
                return FlowSignal(ftype=FlowSignal.EXECUTE)
        else:
            self.__expr()

            if saveval:
                return FlowSignal(ftarget=self.__operand_stack.pop())

 
        while self.__tokenindex < len(self.__tokenlist) and self.__token.category != Token.ELSE:
            self.__advance()

        if self.__token.category == Token.ELSE:
            self.__advance()

            if self.__token.category != Token.UNSIGNEDINT:
                return FlowSignal(ftype=FlowSignal.EXECUTE)
            else:

                self.__expr()

                return FlowSignal(ftarget=self.__operand_stack.pop())

        else:
            return None

    def __forstmt(self):
        step = 1

        self.__advance()  

        loop_variable = self.__token.lexeme  

        self.__advance()  
        self.__consume(Token.ASSIGNOP)
        self.__expr()

        start_val = self.__operand_stack.pop()

        self.__consume(Token.TO)

        self.__expr()
        end_val = self.__operand_stack.pop()

        increment = True
        if not self.__tokenindex >= len(self.__tokenlist):
            self.__consume(Token.STEP)

            self.__expr()
            step = self.__operand_stack.pop()

            if step == 0:
                raise IndexError('Zero step value supplied for loop' +
                                 ' in line ' + str(self.__line_number))

            elif step < 0:
                increment = False

        from_next = False
        if self.last_flowsignal:
            if self.last_flowsignal.ftype == FlowSignal.LOOP_REPEAT:
                from_next = True

        if not from_next:
            self.__symbol_table[loop_variable] = start_val

        else:
            self.__symbol_table[loop_variable] += step
        stop = False
        if increment and self.__symbol_table[loop_variable] > end_val:
            stop = True

        elif not increment and self.__symbol_table[loop_variable] < end_val:
            stop = True

        if stop:
            return FlowSignal(ftype=FlowSignal.LOOP_SKIP,
                              ftarget=loop_variable)
        else:
            return FlowSignal(ftype=FlowSignal.LOOP_BEGIN,floop_var=loop_variable)

    def __nextstmt(self):
        self.__advance()  
        loop_variable = self.__token.lexeme  

        if loop_variable.endswith('$'):
            raise SyntaxError('Syntax error: Loop variable is not numeric' +
                              ' in line ' + str(self.__line_number))

        return FlowSignal(ftype=FlowSignal.LOOP_REPEAT,floop_var=loop_variable)

    def __relexpr(self):
        self.__expr()
        if self.__token.category == Token.ASSIGNOP:
            self.__token.category = Token.EQUAL

        if self.__token.category in [Token.LESSER, Token.GREATER, Token.EQUAL, Token.NOTEQUAL]:
            savecat = self.__token.category
            self.__advance()
            self.__expr()

            right = self.__operand_stack.pop()
            left = self.__operand_stack.pop()

            if savecat == Token.EQUAL:
                self.__operand_stack.append(left == right)  

            elif savecat == Token.NOTEQUAL:
                self.__operand_stack.append(left != right)  

            elif savecat == Token.LESSER:
                self.__operand_stack.append(left < right) 

            elif savecat == Token.GREATER:
                self.__operand_stack.append(left > right)  

    def __logexpr(self):
        self.__notexpr()

        while self.__token.category in [Token.OR, Token.AND]:
            savecat = self.__token.category
            self.__advance()
            self.__notexpr()

            right = self.__operand_stack.pop()
            left = self.__operand_stack.pop()

            if savecat == Token.OR:
                self.__operand_stack.append(left or right)  # Push True or False

            elif savecat == Token.AND:
                self.__operand_stack.append(left and right)  # Push True or False

    def __notexpr(self):
        if self.__token.category == Token.NOT:
            self.__advance()
            self.__relexpr()
            right = self.__operand_stack.pop()
            self.__operand_stack.append(not right)
        else:
            self.__relexpr()

    def __evaluate_function(self, category):
        self.__advance()  

        if category == Token.LEFT:
            self.__consume(Token.LEFTPAREN)

            self.__expr()
            instring = self.__operand_stack.pop()

            self.__consume(Token.COMMA)

            self.__expr()
            chars = self.__operand_stack.pop()

            self.__consume(Token.RIGHTPAREN)

            return instring[:chars]

        if category == Token.RIGHT:
            self.__consume(Token.LEFTPAREN)
            self.__expr()
            instring = self.__operand_stack.pop()
            self.__consume(Token.COMMA)
            self.__expr()
            chars = self.__operand_stack.pop()
            self.__consume(Token.RIGHTPAREN)

            return instring[-chars:]

        

        self.__consume(Token.LEFTPAREN)

        self.__expr()
        value = self.__operand_stack.pop()

        self.__consume(Token.RIGHTPAREN)

        if category == Token.INT:

            return math.floor(value)

        elif category == Token.STR:
            return str(value)

        elif category == Token.VAL:
            numeric = float(value)
            if numeric.is_integer():
                return int(numeric)
            return numeric

        elif category == Token.LEN:
            len(value)

        elif category == Token.TAB:
            if isinstance(value, int):
                return " "*value