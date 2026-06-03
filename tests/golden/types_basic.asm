.ORIG x3000
    LD R6, STACK_TOP
    AND R5, R5, #0
    JSR main
    HALT
main
    ADD R6, R6, #-1
    STR R5, R6, #0
    ADD R5, R6, #0
    ADD R6, R6, #-1
    STR R1, R6, #0
    ADD R6, R6, #-1
    STR R4, R6, #0
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    LD R0, LC_INT_0
    STR R0, R5, #-3
    AND R0, R0, #0
    STR R0, R5, #-4
    LD R0, LC_INT_1
    STR R0, R5, #-5
    AND R0, R0, #0
    ADD R0, R0, #1
    STR R0, R5, #-6
    ADD R0, R5, #-3
    STR R0, R5, #-4
    LDR R0, R5, #-4
    LDR R0, R0, #0
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-5
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    LDR R1, R5, #-4
    STR R0, R1, #0
    LDR R0, R5, #-3
    LEA R4, G_result
    STR R0, R4, #0
    AND R0, R0, #0
    LDR R1, R5, #-1
    LDR R4, R5, #-2
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
G_result .FILL #0
LC_INT_0 .FILL #42
LC_INT_1 .FILL #65
.END
