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
    AND R0, R0, #0
    STR R0, R5, #-2
while_test_5
    GETC
    STR R0, R5, #-2
    LDR R0, R5, #-2
    AND R1, R1, #0
    ADD R1, R1, #10
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRnp ifend_7
    BRnzp while_end_6
ifend_7
    LDR R0, R5, #-2
    OUT
    AND R0, R0, #0
    BRnzp while_test_5
while_end_6
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    LDR R1, R5, #-1
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
.END
