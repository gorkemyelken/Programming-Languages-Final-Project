from basictoken import BASICToken as Token
from lexer import Lexer
from program import Program

def main():

    lexer = Lexer()
    program = Program()

    while True:

        stmt = input('>>> ')

        tokenlist = lexer.tokenize(stmt)
        if len(tokenlist) > 0:
            if tokenlist[0].category == Token.EXIT:
                break
            elif tokenlist[0].category == Token.UNSIGNEDINT\
                and len(tokenlist) > 1:
                program.add_stmt(tokenlist)
            elif tokenlist[0].category == Token.UNSIGNEDINT \
                    and len(tokenlist) == 1:
                program.delete_statement(int(tokenlist[0].lexeme))
            elif tokenlist[0].category == Token.RUN:
                program.execute()

if __name__ == "__main__":
    main()