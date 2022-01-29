class BASICToken:
        LET             = 1   # LET keyword
        PRINT           = 3   # PRINT command
        RUN             = 4   # RUN command
        FOR             = 5   # FOR keyword
        NEXT            = 6   # NEXT keyword
        IF              = 7   # IF keyword
        THEN            = 8   # THEN keyword
        ELSE            = 9   # ELSE keyword
        ASSIGNOP        = 10  # '='
        LEFTPAREN       = 11  # '('
        RIGHTPAREN      = 12  # ')'
        PLUS            = 13  # '+'
        MINUS           = 14  # '-'
        TIMES           = 15  # '*'
        DIVIDE          = 16  # '/'
        NEWLINE         = 17  # End of line
        UNSIGNEDINT     = 18  # Integer
        NAME            = 19  # Identifier that is not a keyword
        EXIT            = 20  # Used to quit the interpreter
        GREATER         = 21  # '>'
        LESSER          = 22  # '<'
        STEP            = 23  # STEP keyword
        RETURN          = 25  # RETURN keyword
        NOTEQUAL        = 26  # '<>'
        UNSIGNEDFLOAT   = 27  # Floating point number
        STRING          = 28  # String values
        TO              = 29  # TO keyword
        NEW             = 30  # NEW command
        EQUAL           = 31  # '='
        COMMA           = 32  # ','
        STOP            = 33  # STOP keyword
        COLON           = 34  # ':'
        ON              = 35  # ON keyword 
        DATA            = 36  # DATA keyword
        INT             = 37  # INT function        
        STR             = 38  # STR$ function
        MODULO          = 39  # MODULO operator
        VAL             = 40  # VAL function
        LEN             = 41  # LEN function
        AND             = 42  # AND operator
        OR              = 43  # OR operator
        NOT             = 44  # NOT operator
        HASH            = 45  # "#"
        TAB             = 46  # TAB function
        SEMICOLON       = 47  # SEMICOLON
        LEFT            = 48  # LEFT$ function
        RIGHT           = 49  # RIGHT$ function

        catnames = ['LET', 'PRINT', 'RUN',
        'FOR', 'NEXT', 'IF', 'THEN', 'ELSE', 'ASSIGNOP',
        'LEFTPAREN', 'RIGHTPAREN', 'PLUS', 'MINUS', 'TIMES',
        'DIVIDE', 'NEWLINE', 'UNSIGNEDINT', 'NAME', 'EXIT',
        'GREATER', 'LESSER', 'STEP', 'RETURN', 
        'NOTEQUAL', 'TO', 'UNSIGNEDFLOAT', 'STRING', 'NEW', 'EQUAL',
        'COMMA', 'STOP', 'COLON','ON','DATA', 'INT','MODULO',
        'VAL', 'LEN','AND', 'OR', 'NOT', 'HASH', 'TAB', 'SEMICOLON',
        'LEFT', 'RIGHT']

        smalltokens = {'=': ASSIGNOP, '(': LEFTPAREN, ')': RIGHTPAREN,
                       '+': PLUS, '-': MINUS, '*': TIMES, '/': DIVIDE,
                       '\n': NEWLINE, '<': LESSER,
                       '>': GREATER, '<>': NOTEQUAL,
                       ',': COMMA,
                       ':': COLON, '%': MODULO, '!=': NOTEQUAL, '#': HASH,
                       ';': SEMICOLON}

        keywords = {'LET': LET, 'PRINT': PRINT,
                    'FOR': FOR, 'RUN': RUN, 'NEXT': NEXT,
                    'IF': IF, 'THEN': THEN, 'ELSE': ELSE,
                    'EXIT': EXIT, 'STEP': STEP,
                    'ON':ON, 'RETURN': RETURN,
                    'NEW': NEW,'STOP': STOP, 'TO': TO,
                    'DATA': DATA, 'INT': INT,'STR$': STR,'MOD': MODULO,
                    'VAL': VAL, 'LEN': LEN,
                    'END': STOP,'AND': AND, 'OR': OR, 'NOT': NOT,
                    'TAB': TAB,'LEFT$': LEFT, 'RIGHT$': RIGHT}

        functions = {INT,STR, VAL, LEN, TAB, LEFT, RIGHT}

        def __init__(self, column, category, lexeme):

            self.column = column      
            self.category = category  
            self.lexeme = lexeme      