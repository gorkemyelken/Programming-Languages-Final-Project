from basictoken import BASICToken as Token
from basicparser import BASICParser
from flowsignal import FlowSignal
from lexer import Lexer


class BASICData:
    def __init__(self):
        self.__datastmts = {}
        self.__next_data = 0

    def delete(self):
        self.__datastmts.clear()
        self.__next_data = 0

    def delData(self,line_number):
        if self.__datastmts.get(line_number) != None:
            del self.__datastmts[line_number]

    def addData(self,line_number,tokenlist):
        self.__datastmts[line_number] = tokenlist

    def getTokens(self,line_number):
        return self.__datastmts.get(line_number)

    def readData(self,read_line_number):
        if len(self.__datastmts) == 0:
            raise RuntimeError('No DATA statements available to READ ' +
                               'in line ' + str(read_line_number))
        data_values = []
        line_numbers = list(self.__datastmts.keys())
        line_numbers.sort()
        if self.__next_data == 0:
            self.__next_data = line_numbers[0]
        elif line_numbers.index(self.__next_data) < len(line_numbers)-1:
            self.__next_data = line_numbers[line_numbers.index(self.__next_data)+1]
        else:
            raise RuntimeError('No DATA statements available to READ ' +
                               'in line ' + str(read_line_number))
        tokenlist = self.__datastmts[self.__next_data]
        sign = 1
        for token in tokenlist[1:]:
            if token.category != Token.COMMA:
                if token.category == Token.STRING:
                    data_values.append(token.lexeme)
                elif token.category == Token.UNSIGNEDINT:
                    data_values.append(sign*int(token.lexeme))
                elif token.category == Token.UNSIGNEDFLOAT:
                    data_values.append(sign*eval(token.lexeme))
                elif token.category == Token.MINUS:
                    sign = -1
            else:
                sign = 1
        return data_values

    def restore(self,restoreLineNo):
        if restoreLineNo == 0 or restoreLineNo in self.__datastmts:

            if restoreLineNo == 0:
                self.__next_data = restoreLineNo
            else:

                line_numbers = list(self.__datastmts.keys())
                line_numbers.sort()

                indexln = line_numbers.index(restoreLineNo)

                if indexln == 0:
                    self.__next_data = 0
                else:
                    self.__next_data = line_numbers[indexln-1]

class Program:

    def __init__(self):
        self.__program = {}
        self.__next_stmt = 0
        self.__return_stack = []
        self.__return_loop = {}
        self.__data = BASICData()

    def __str__(self):

        program_text = ""
        line_numbers = self.line_numbers()

        for line_number in line_numbers:
            program_text += self.str_statement(line_number)

        return program_text

    def str_statement(self, line_number):
        line_text = str(line_number) + " "

        statement = self.__program[line_number]
        if statement[0].category == Token.DATA:
            statement = self.__data.getTokens(line_number)
        for token in statement:
            if token.category == Token.STRING:
                line_text += '"' + token.lexeme + '" '

            else:
                line_text += token.lexeme + " "
        line_text += "\n"
        return line_text

    def list(self, start_line=None, end_line=None):
        line_numbers = self.line_numbers()
        if not start_line:
            start_line = int(line_numbers[0])

        if not end_line:
            end_line = int(line_numbers[-1])

        for line_number in line_numbers:
            if int(line_number) >= start_line and int(line_number) <= end_line:
                print(self.str_statement(line_number), end="")

    def add_stmt(self, tokenlist):
        try:
            line_number = int(tokenlist[0].lexeme)
            if tokenlist[1].lexeme == "DATA":
                self.__data.addData(line_number,tokenlist[1:])
                self.__program[line_number] = [tokenlist[1],]
            else:
                self.__program[line_number] = tokenlist[1:]

        except TypeError as err:
            raise TypeError("Invalid line number: " +
                            str(err))

    def line_numbers(self):
        line_numbers = list(self.__program.keys())
        line_numbers.sort()

        return line_numbers

    def __execute(self, line_number):
        if line_number not in self.__program.keys():
            raise RuntimeError("Line number " + line_number +
                               " does not exist")

        statement = self.__program[line_number]

        try:
            return self.__parser.parse(statement, line_number)

        except RuntimeError as err:
            raise RuntimeError(str(err))

    def execute(self):
        self.__parser = BASICParser(self.__data)
        self.__data.restore(0)
        line_numbers = self.line_numbers()
        if len(line_numbers) > 0:
            index = 0
            self.set_next_line_number(line_numbers[index])
            while True:
                flowsignal = self.__execute(self.get_next_line_number())
                self.__parser.last_flowsignal = flowsignal

                if flowsignal:
                    if flowsignal.ftype == FlowSignal.SIMPLE_JUMP:
                        index = line_numbers.index(flowsignal.ftarget)
                        self.set_next_line_number(flowsignal.ftarget)

                    elif flowsignal.ftype == FlowSignal.GOSUB:
                        if index + 1 < len(line_numbers):
                            self.__return_stack.append(line_numbers[index + 1])

                        else:
                            raise RuntimeError("GOSUB at end of program, nowhere to return")
                        
                        index = line_numbers.index(flowsignal.ftarget)

                        self.set_next_line_number(flowsignal.ftarget)

                    elif flowsignal.ftype == FlowSignal.RETURN:
                        index = line_numbers.index(self.__return_stack.pop())
                        self.set_next_line_number(line_numbers[index])

                    elif flowsignal.ftype == FlowSignal.STOP:
                        break

                    elif flowsignal.ftype == FlowSignal.LOOP_BEGIN:
                        self.__return_loop[flowsignal.floop_var] = line_numbers[index]
                        index = index + 1

                        if index < len(line_numbers):
                            self.set_next_line_number(line_numbers[index])

                    elif flowsignal.ftype == FlowSignal.LOOP_SKIP:
                        index = index + 1
                        while index < len(line_numbers):
                            next_line_number = line_numbers[index]
                            temp_tokenlist = self.__program[next_line_number]

                            if temp_tokenlist[0].category == Token.NEXT and \
                               len(temp_tokenlist) > 1:
                                if temp_tokenlist[1].lexeme == flowsignal.ftarget:
                                    index = index + 1
                                    if index < len(line_numbers):
                                        next_line_number = line_numbers[index]
                                        self.set_next_line_number(next_line_number)
                                        break

                            index = index + 1
                        if index >= len(line_numbers):
                            break

                    elif flowsignal.ftype == FlowSignal.LOOP_REPEAT:
                        index = line_numbers.index(self.__return_loop.pop(flowsignal.floop_var))
                        self.set_next_line_number(line_numbers[index])

                else:
                    index = index + 1
                    if index < len(line_numbers):
                        self.set_next_line_number(line_numbers[index])
                    else:
                        break

        else:
            raise RuntimeError("No statements to execute")

    def delete(self):
        self.__program.clear()
        self.__data.delete()

    def delete_statement(self, line_number):
        self.__data.delData(line_number)
        del self.__program[line_number]

    def get_next_line_number(self):
        return self.__next_stmt

    def set_next_line_number(self, line_number):
        self.__next_stmt = line_number