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
    STR R2, R6, #0
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    AND R0, R0, #0
    STR R0, R5, #-3
    STR R0, R5, #-5
    STR R0, R5, #-9
    AND R0, R0, #0
    STR R0, R5, #-3
    AND R0, R0, #0
    ADD R0, R0, #1
    STR R0, R5, #-4
    AND R0, R0, #0
    STR R0, R5, #-5
    LDR R0, R5, #-3
    ADD R0, R0, #0
    BRnp or_skip_11
    LDR R0, R5, #-4
    ADD R0, R0, #0
    BRz else_9
    LDR R0, R5, #-5
    ADD R0, R0, #0
    BRz else_9
or_skip_11
    LD R0, LC_INT_0
    OUT
    AND R0, R0, #0
    BRnzp ifend_10
else_9
    LD R0, LC_INT_1
    OUT
    AND R0, R0, #0
ifend_10
    AND R0, R0, #0
    ADD R0, R0, #14
    STR R0, R5, #-6
    LD R0, LC_INT_2
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-6
    ADD R6, R6, #-1
    STR R1, R6, #0
    AND R2, R2, #0
    ADD R2, R2, #14
    LDR R1, R6, #0
    ADD R6, R6, #1
    NOT R2, R2
    ADD R2, R2, #1
    ADD R2, R1, R2
    BRz cmp_true_12
    AND R1, R1, #0
    BRnzp cmp_end_13
cmp_true_12
    AND R1, R1, #0
    ADD R1, R1, #1
cmp_end_13
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    ADD R0, R0, #5
    STR R0, R5, #-7
    AND R0, R0, #0
    ADD R0, R0, #3
    STR R0, R5, #-8
    LDR R0, R5, #-7
    AND R1, R1, #0
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRnz else_14
    LDR R0, R5, #-8
    AND R1, R1, #0
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRzp else_14
    LD R0, LC_INT_0
    OUT
    AND R0, R0, #0
    BRnzp ifend_15
else_14
    LD R0, LC_INT_1
    OUT
    AND R0, R0, #0
ifend_15
    AND R0, R0, #0
    STR R0, R5, #-9
    LDR R0, R5, #-7
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-8
    LDR R0, R6, #0
    ADD R6, R6, #1
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRp cmp_true_16
    AND R0, R0, #0
    BRnzp cmp_end_17
cmp_true_16
    AND R0, R0, #0
    ADD R0, R0, #1
cmp_end_17
    STR R0, R5, #-9
    LD R0, LC_INT_2
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-9
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    LDR R1, R5, #-1
    LDR R2, R5, #-2
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    LDR R7, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
LC_INT_0 .FILL #78
LC_INT_1 .FILL #89
LC_INT_2 .FILL #48
.END
