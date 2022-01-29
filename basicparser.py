from basictoken import BASICToken as Token
from flowsignal import FlowSignal
import math
import random
from time import monotonic

class BASICParser:

    def __init__(self, basicdata):
        self.__symbol_table = {}
        self.__operand_stack = []
        self.__data = basicdata
        self.__data_values = []
        self.__tokenlist = []
        self.__tokenindex = None
        self.last_flowsignal = None
        self.__prnt_column = 0
        self.__file_handles = {}

    def parse(self, tokenlist, line_number):
        self.__line_number = line_number
        self.__tokenlist = []
        self.__tokenindex = 0
        linetokenindex = 0
        for token in tokenlist:
            if token.category == token.IF:
                linetokenindex += self.__tokenindex
                self.__tokenindex = 0
                self.__tokenlist = tokenlist[linetokenindex:]
                self.__token = self.__tokenlist[0]
                flow = self.__stmt()
                if flow and (flow.ftype == FlowSignal.EXECUTE):
                    try:
                        return self.parse(tokenlist[linetokenindex+self.__tokenindex:],line_number)
                    except RuntimeError as err:
                        raise RuntimeError(str(err)+' in line ' + str(self.__line_number))
                else:
                    return flow
            elif token.category == token.COLON:
                linetokenindex += self.__tokenindex
                self.__tokenindex = 0
                self.__token = self.__tokenlist[self.__tokenindex]

                flow = self.__stmt()
                if flow:
                    return flow

                linetokenindex += 1
                self.__tokenlist = []
            elif token.category == token.ELSE:
                break
            else:
                self.__tokenlist.append(token)

        linetokenindex += self.__tokenindex
        self.__tokenindex = 0
        self.__token = self.__tokenlist[self.__tokenindex]
        return self.__stmt()

    def __advance(self):
        self.__tokenindex += 1
        if not self.__tokenindex >= len(self.__tokenlist):
            self.__token = self.__tokenlist[self.__tokenindex]

    def __consume(self, expected_category):
        if self.__token.category == expected_category:
            self.__advance()

    def __stmt(self):
        if self.__token.category in [Token.FOR, Token.IF, Token.NEXT, Token.ON]:
            return self.__compoundstmt()

        else:
            return self.__simplestmt()

    def __simplestmt(self):
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
        self.__advance()   

        fileIO = False
        if self.__token.category == Token.HASH:
            fileIO = True

            self.__consume(Token.HASH)

            self.__expr()
            filenum = self.__operand_stack.pop()

            if self.__tokenindex < len(self.__tokenlist) and self.__token.category != Token.COLON:
                self.__consume(Token.COMMA)

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

        if fileIO:
            self.__file_handles[filenum].write("\n")
        else:
            print()
        self.__prnt_column = 0

    def __letstmt(self):
        self.__advance() 
        self.__assignmentstmt()


    def __returnstmt(self):
        self.__advance() 
        return FlowSignal(ftype=FlowSignal.RETURN)

    def __stopstmt(self):
        self.__advance()

        for handles in self.__file_handles:
            self.__file_handles[handles].close()
        self.__file_handles.clear()

        return FlowSignal(ftype=FlowSignal.STOP)

    def __assignmentstmt(self):
        left = self.__token.lexeme  
                               
        self.__advance()

        if self.__token.category == Token.LEFTPAREN:
            self.__arrayassignmentstmt(left)

        else:
            self.__consume(Token.ASSIGNOP)
            self.__logexpr()
            right = self.__operand_stack.pop()

            self.__symbol_table[left] = right

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
            savesign = self.__sign
            self.__logexpr()

            if savesign == -1:
                self.__operand_stack[-1] = -self.__operand_stack[-1]

            self.__consume(Token.RIGHTPAREN)

        elif self.__token.category in Token.functions:
            self.__operand_stack.append(self.__evaluate_function(self.__token.category))

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