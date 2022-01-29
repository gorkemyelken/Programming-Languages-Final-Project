class FlowSignal:
    SIMPLE_JUMP        = 0
    GOSUB              = 1
    LOOP_BEGIN         = 2
    LOOP_REPEAT        = 3
    LOOP_SKIP          = 4
    RETURN             = 5
    STOP               = 6
    EXECUTE            = 7

    def __init__(self, ftarget=None, ftype=SIMPLE_JUMP, floop_var=None):
        if ftype not in [self.GOSUB, self.SIMPLE_JUMP, self.LOOP_BEGIN,
                         self.LOOP_REPEAT, self.RETURN,
                         self.LOOP_SKIP, self.STOP, self.EXECUTE]:
            raise TypeError("Invalid flow signal type supplied: " + str(ftype))
        if ftarget == None and \
           ftype in [self.SIMPLE_JUMP, self.GOSUB, self.LOOP_SKIP]:
            raise TypeError("Invalid jump target supplied for flow signal type: " + str(ftarget))
        if ftarget != None and \
           ftype in [self.RETURN, self.LOOP_BEGIN, self.LOOP_REPEAT,
                     self.STOP, self.EXECUTE]:
            raise TypeError("Target wrongly supplied for flow signal " + str(ftype))
        self.ftype = ftype
        self.ftarget = ftarget
        self.floop_var = floop_var