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
    STR R4, R6, #0
    ADD R6, R6, #-1
    STR R3, R6, #0
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    ADD R6, R6, #-1
    AND R0, R0, #0
    STR R0, R5, #-6
    STR R0, R5, #-7
    AND R0, R0, #0
    STR R0, R5, #-6
while_test_14
    LDR R0, R5, #-6
    AND R1, R1, #0
    ADD R1, R1, #5
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRzp while_end_15
    LDR R1, R5, #-6
    ADD R6, R6, #-1
    STR R1, R6, #0
    LDR R0, R5, #-6
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R1, R1, #0
    ADD R1, R1, #1
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    LDR R1, R6, #0
    ADD R6, R6, #1
    ADD R2, R5, #-5
    ADD R2, R2, R1
    STR R0, R2, #0
    LDR R0, R5, #-6
    ADD R0, R0, #1
    STR R0, R5, #-6
    BRnzp while_test_14
while_end_15
    AND R0, R0, #0
    STR R0, R5, #-7
    AND R0, R0, #0
    STR R0, R5, #-6
while_test_16
    LDR R0, R5, #-6
    AND R1, R1, #0
    ADD R1, R1, #5
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRzp while_end_17
    LDR R0, R5, #-7
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-6
    ADD R2, R5, #-5
    ADD R2, R2, R1
    LDR R1, R2, #0
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    STR R0, R5, #-7
    LDR R0, R5, #-6
    ADD R0, R0, #1
    STR R0, R5, #-6
    BRnzp while_test_16
while_end_17
    LDR R0, R5, #-7
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R1, R1, #0
    ADD R1, R1, #10
    LDR R0, R6, #0
    ADD R6, R6, #1
    AND R4, R4, #0
    ADD R3, R0, #0
    ADD R0, R0, #0
    BRzp mul_left_ok_18
    NOT R0, R0
    ADD R0, R0, #1
    ADD R4, R4, #1
mul_left_ok_18
    ADD R1, R1, #0
    BRzp mul_right_ok_19
    NOT R1, R1
    ADD R1, R1, #1
    ADD R4, R4, #1
mul_right_ok_19
    ADD R3, R0, #0
    AND R4, R4, #1
    ADD R0, R4, #0
    AND R2, R2, #0
    ADD R1, R1, #0
    BRz div_done_21
div_loop_20
    NOT R4, R1
    ADD R4, R4, #1
    ADD R4, R3, R4
    BRn div_done_21
    ADD R3, R4, #0
    ADD R2, R2, #1
    BRnzp div_loop_20
div_done_21
    ADD R0, R0, #0
    BRz sign_ok_22
    NOT R2, R2
    ADD R2, R2, #1
sign_ok_22
    ADD R0, R2, #0
    ADD R6, R6, #-1
    STR R0, R6, #0
    LD R1, LC_INT_0
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    LDR R0, R5, #-7
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R1, R1, #0
    ADD R1, R1, #10
    LDR R0, R6, #0
    ADD R6, R6, #1
    AND R4, R4, #0
    ADD R3, R0, #0
    ADD R0, R0, #0
    BRzp mul_left_ok_23
    NOT R0, R0
    ADD R0, R0, #1
    ADD R4, R4, #1
mul_left_ok_23
    ADD R1, R1, #0
    BRzp mul_right_ok_24
    NOT R1, R1
    ADD R1, R1, #1
    ADD R4, R4, #1
mul_right_ok_24
    ADD R3, R0, #0
    AND R4, R4, #1
    ADD R0, R4, #0
    AND R2, R2, #0
    ADD R1, R1, #0
    BRz div_done_26
div_loop_25
    NOT R4, R1
    ADD R4, R4, #1
    ADD R4, R3, R4
    BRn div_done_26
    ADD R3, R4, #0
    ADD R2, R2, #1
    BRnzp div_loop_25
div_done_26
    ADD R0, R0, #0
    BRz sign_ok_27
    NOT R3, R3
    ADD R3, R3, #1
sign_ok_27
    ADD R0, R3, #0
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
    LDR R2, R5, #-2
    LDR R4, R5, #-3
    LDR R3, R5, #-4
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    LDR R7, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
LC_INT_0 .FILL #48
.END
