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
    AND R0, R0, #0
    ADD R0, R0, #4
    STR R0, R5, #-3
    AND R0, R0, #0
    ADD R0, R0, #7
    STR R0, R5, #-4
    LDR R0, R5, #-3
    LDR R1, R5, #-4
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRnz else_6
    AND R0, R0, #0
    ADD R0, R0, #1
    LEA R4, G_result
    STR R0, R4, #0
    BRnzp ifend_7
else_6
    LDR R0, R5, #-3
    AND R1, R1, #0
    ADD R1, R1, #3
    ADD R0, R0, R1
    LDR R1, R5, #-4
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRnp else_8
    AND R0, R0, #0
    ADD R0, R0, #2
    LEA R4, G_result
    STR R0, R4, #0
    BRnzp ifend_9
else_8
    AND R0, R0, #0
    ADD R0, R0, #3
    LEA R4, G_result
    STR R0, R4, #0
ifend_9
ifend_7
    AND R0, R0, #0
    LDR R1, R5, #-1
    LDR R4, R5, #-2
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
G_result .FILL #0
.END
