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
    ADD R0, R0, #3
    STR R0, R5, #-3
    AND R0, R0, #0
    ADD R0, R0, #5
    STR R0, R5, #-4
    AND R0, R0, #0
    STR R0, R5, #-5
    LDR R0, R5, #-3
    LDR R1, R5, #-4
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRzp ifend_8
    LDR R0, R5, #-5
    ADD R0, R0, #1
    STR R0, R5, #-5
ifend_8
    LDR R0, R5, #-3
    AND R1, R1, #0
    ADD R1, R1, #3
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRp ifend_9
    LDR R0, R5, #-5
    ADD R0, R0, #2
    STR R0, R5, #-5
ifend_9
    LDR R0, R5, #-4
    LDR R1, R5, #-3
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRnz ifend_10
    LDR R0, R5, #-5
    ADD R0, R0, #4
    STR R0, R5, #-5
ifend_10
    LDR R0, R5, #-4
    AND R1, R1, #0
    ADD R1, R1, #5
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRn ifend_11
    LDR R0, R5, #-5
    ADD R0, R0, #8
    STR R0, R5, #-5
ifend_11
    LDR R0, R5, #-3
    AND R1, R1, #0
    ADD R1, R1, #3
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRnp ifend_12
    LDR R0, R5, #-5
    LD R1, LC_INT_0
    ADD R0, R0, R1
    STR R0, R5, #-5
ifend_12
    LDR R0, R5, #-3
    LDR R1, R5, #-4
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRz ifend_13
    LDR R0, R5, #-5
    LD R1, LC_INT_1
    ADD R0, R0, R1
    STR R0, R5, #-5
ifend_13
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
LC_INT_0 .FILL #16
LC_INT_1 .FILL #32
.END
