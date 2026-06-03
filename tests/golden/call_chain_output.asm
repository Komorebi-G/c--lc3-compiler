.ORIG x3000
    LD R6, STACK_TOP
    AND R5, R5, #0
    JSR main
    HALT
main
    ADD R6, R6, #-1
    STR R7, R6, #0
    ADD R6, R6, #-1
    STR R5, R6, #0
    ADD R5, R6, #0
    ADD R6, R6, #-1
    STR R1, R6, #0
    ADD R6, R6, #-1
    AND R0, R0, #0
    ADD R0, R0, #3
    ADD R6, R6, #-1
    STR R0, R6, #0
    JSR FN_twice
    ADD R6, R6, #1
    ADD R6, R6, #-1
    STR R0, R6, #0
    JSR FN_bump3
    ADD R6, R6, #1
    STR R0, R5, #-2
    LDR R0, R5, #-2
    ADD R6, R6, #-1
    STR R0, R6, #0
    LD R1, LC_INT_0
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    LDR R1, R5, #-1
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    LDR R7, R6, #0
    ADD R6, R6, #1
    RET
FN_add
    ADD R6, R6, #-1
    STR R5, R6, #0
    ADD R5, R6, #0
    ADD R6, R6, #-1
    STR R1, R6, #0
    LDR R0, R5, #1
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #2
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    LDR R1, R5, #-1
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    RET
FN_twice
    ADD R6, R6, #-1
    STR R7, R6, #0
    ADD R6, R6, #-1
    STR R5, R6, #0
    ADD R5, R6, #0
    LDR R0, R5, #2
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R0, R5, #2
    ADD R6, R6, #-1
    STR R0, R6, #0
    JSR FN_add
    ADD R6, R6, #2
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    LDR R7, R6, #0
    ADD R6, R6, #1
    RET
FN_bump3
    ADD R6, R6, #-1
    STR R7, R6, #0
    ADD R6, R6, #-1
    STR R5, R6, #0
    ADD R5, R6, #0
    AND R0, R0, #0
    ADD R0, R0, #3
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R0, R5, #2
    ADD R6, R6, #-1
    STR R0, R6, #0
    JSR FN_add
    ADD R6, R6, #2
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    LDR R7, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
LC_INT_0 .FILL #48
.END
