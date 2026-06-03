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
    STR R4, R6, #0
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    AND R0, R0, #0
    STR R0, R5, #-2
    STR R0, R5, #-4
    AND R0, R0, #0
    STR R0, R5, #-2
    AND R0, R0, #0
    ADD R0, R0, #1
    STR R0, R5, #-3
    AND R0, R0, #0
    STR R0, R5, #-4
    LDR R0, R5, #-2
    ADD R0, R0, #0
    BRnp or_skip_5
    LDR R0, R5, #-3
    ADD R0, R0, #0
    BRz else_3
    LDR R0, R5, #-4
    ADD R0, R0, #0
    BRz else_3
or_skip_5
    AND R0, R0, #0
    ADD R0, R0, #1
    LEA R4, G_result
    STR R0, R4, #0
    BRnzp ifend_4
else_3
    AND R0, R0, #0
    ADD R0, R0, #2
    LEA R4, G_result
    STR R0, R4, #0
ifend_4
    AND R0, R0, #0
    LDR R4, R5, #-1
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
G_result .FILL #0
.END
