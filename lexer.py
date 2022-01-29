from basictoken import BASICToken as Token

class Lexer:

    def __init__(self):

        self.__column = 0 
        self.__stmt = ''   

    def tokenize(self, stmt):
        self.__stmt = stmt
        self.__column = 0
        tokenlist = []

        c = self.__get_next_char()
        while c != '':
            while c.isspace():
                c = self.__get_next_char()

            token = Token(self.__column - 1, None, '')

            if c == '"':
                token.category = Token.STRING
                c = self.__get_next_char()  
                if c == '"':
                    c = self.__get_next_char()

                else:
                    while True:
                        token.lexeme += c  
                        c = self.__get_next_char()

                        if c == '':
                            raise SyntaxError("Mismatched quotes")

                        if c == '"':
                            c = self.__get_next_char()
                            break

            elif c.isdigit():
                token.category = Token.UNSIGNEDINT
                found_point = False
                while True:
                    token.lexeme += c 
                    c = self.__get_next_char()
                    if not c.isdigit():
                        if c == '.':
                            if not found_point:
                                found_point = True
                                token.category = Token.UNSIGNEDFLOAT

                            else:
                                break

                        else:
                            break

            elif c.isalpha():
                while True:
                    token.lexeme += c  
                    c = self.__get_next_char()
                    if not ((c.isalpha() or c.isdigit()) or c == '_' or c == '$'):
                        break

                token.lexeme = token.lexeme.upper()
                if token.lexeme in Token.keywords:
                    token.category = Token.keywords[token.lexeme]

                else:
                    token.category = Token.NAME

            elif c in Token.smalltokens:
                save = c
                c = self.__get_next_char()  
                twochar = save + c

                if twochar in Token.smalltokens:
                    token.category = Token.smalltokens[twochar]
                    token.lexeme = twochar
                    c = self.__get_next_char()

                else:
                    token.category = Token.smalltokens[save]
                    token.lexeme = save

            elif c != '':
                raise SyntaxError('Syntax error')
            tokenlist.append(token)

        return tokenlist

    def __get_next_char(self):
        if self.__column < len(self.__stmt):
            next_char = self.__stmt[self.__column]
            self.__column = self.__column + 1

            return next_char

        else:
            return ''


if __name__ == "__main__":
    import doctest
    doctest.testmod()