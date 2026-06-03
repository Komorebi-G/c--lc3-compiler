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
    AND R0, R0, #0
    STR R0, R5, #-5
    AND R0, R0, #0
    ADD R0, R0, #5
    STR R0, R5, #-3
    AND R0, R0, #0
    ADD R0, R0, #3
    STR R0, R5, #-4
    AND R0, R0, #0
    STR R0, R5, #-5
    LDR R0, R5, #-3
    LDR R1, R5, #-4
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRzp else_12
    LD R0, LC_INT_0
    STR R0, R5, #-5
    BRnzp ifend_13
else_12
    LDR R0, R5, #-5
    ADD R0, R0, #1
    STR R0, R5, #-5
ifend_13
    LDR R0, R5, #-3
    AND R1, R1, #0
    ADD R1, R1, #4
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRp else_14
    LD R0, LC_INT_0
    STR R0, R5, #-5
    BRnzp ifend_15
else_14
    LDR R0, R5, #-5
    ADD R0, R0, #2
    STR R0, R5, #-5
ifend_15
    LDR R0, R5, #-4
    LDR R1, R5, #-3
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRnz else_16
    LD R0, LC_INT_0
    STR R0, R5, #-5
    BRnzp ifend_17
else_16
    LDR R0, R5, #-5
    ADD R0, R0, #4
    STR R0, R5, #-5
ifend_17
    LDR R0, R5, #-4
    AND R1, R1, #0
    ADD R1, R1, #5
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRn else_18
    LD R0, LC_INT_0
    STR R0, R5, #-5
    BRnzp ifend_19
else_18
    LDR R0, R5, #-5
    ADD R0, R0, #8
    STR R0, R5, #-5
ifend_19
    LDR R0, R5, #-3
    LDR R1, R5, #-4
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRnp else_20
    LD R0, LC_INT_0
    STR R0, R5, #-5
    BRnzp ifend_21
else_20
    LDR R0, R5, #-5
    ADD R6, R6, #-1
    STR R0, R6, #0
    LD R1, LC_INT_1
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    STR R0, R5, #-5
ifend_21
    LDR R0, R5, #-3
    AND R1, R1, #0
    ADD R1, R1, #5
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRz else_22
    LD R0, LC_INT_0
    STR R0, R5, #-5
    BRnzp ifend_23
else_22
    LDR R0, R5, #-5
    ADD R6, R6, #-1
    STR R0, R6, #0
    LD R1, LC_INT_2
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    STR R0, R5, #-5
ifend_23
    LDR R0, R5, #-5
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
LC_INT_0 .FILL #99
LC_INT_1 .FILL #16
LC_INT_2 .FILL #32
.END
