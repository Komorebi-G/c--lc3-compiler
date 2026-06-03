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
    STR R1, R6, #0
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    AND R0, R0, #0
    STR R0, R5, #-4
    AND R0, R0, #0
    ADD R0, R0, #2
    STR R0, R5, #-3
    AND R0, R0, #0
    STR R0, R5, #-4
    LEA R4, G_enabled
    LDR R0, R4, #0
    ADD R0, R0, #0
    BRz else_2
    LDR R0, R5, #-4
    ADD R0, R0, #0
    BRnp else_2
    LEA R4, G_marker
    LDR R0, R4, #0
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-3
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    LEA R4, G_result
    STR R0, R4, #0
    BRnzp ifend_3
else_2
    AND R0, R0, #0
    ADD R0, R0, #9
    LEA R4, G_result
    STR R0, R4, #0
ifend_3
    AND R0, R0, #0
    LDR R4, R5, #-1
    LDR R1, R5, #-2
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
G_marker .FILL #65
G_enabled .FILL #1
G_result .FILL #0
.END
