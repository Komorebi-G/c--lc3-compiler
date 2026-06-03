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
    AND R0, R0, #0
    STR R0, R5, #-4
    AND R0, R0, #0
    ADD R0, R0, #-5
    STR R0, R5, #-3
    AND R0, R0, #0
    STR R0, R5, #-4
    LD R0, LC_INT_0
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-3
    NOT R1, R1
    ADD R1, R1, #1
    ADD R6, R6, #-1
    STR R1, R6, #0
    AND R2, R2, #0
    ADD R2, R2, #5
    LDR R1, R6, #0
    ADD R6, R6, #1
    NOT R2, R2
    ADD R2, R2, #1
    ADD R2, R1, R2
    BRz cmp_true_10
    AND R1, R1, #0
    BRnzp cmp_end_11
cmp_true_10
    AND R1, R1, #0
    ADD R1, R1, #1
cmp_end_11
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    LD R0, LC_INT_0
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-4
    ADD R1, R1, #0
    BRz not_true_12
    AND R1, R1, #0
    BRnzp not_end_13
not_true_12
    AND R1, R1, #0
    ADD R1, R1, #1
not_end_13
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    LD R0, LC_INT_0
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-3
    ADD R6, R6, #-1
    STR R1, R6, #0
    AND R2, R2, #0
    ADD R2, R2, #5
    LDR R1, R6, #0
    ADD R6, R6, #1
    ADD R1, R1, R2
    ADD R1, R1, #0
    BRz not_true_14
    AND R1, R1, #0
    BRnzp not_end_15
not_true_14
    AND R1, R1, #0
    ADD R1, R1, #1
not_end_15
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    LD R0, LC_INT_0
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R0, R5, #-3
    AND R1, R1, #0
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRzp sc_false_16
    LDR R1, R5, #-4
    ADD R1, R1, #0
    BRz not_true_18
    AND R1, R1, #0
    BRnzp not_end_19
not_true_18
    AND R1, R1, #0
    ADD R1, R1, #1
not_end_19
    ADD R1, R1, #0
    BRz sc_false_16
    AND R1, R1, #0
    ADD R1, R1, #1
    BRnzp sc_end_17
sc_false_16
    AND R1, R1, #0
sc_end_17
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
LC_INT_0 .FILL #48
.END
