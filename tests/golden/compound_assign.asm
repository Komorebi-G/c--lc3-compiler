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
    STR R3, R6, #0
    ADD R6, R6, #-1
    STR R2, R6, #0
    ADD R6, R6, #-1
    AND R0, R0, #0
    ADD R0, R0, #10
    STR R0, R5, #-5
    LDR R0, R5, #-5
    ADD R0, R0, #5
    STR R0, R5, #-5
    LDR R0, R5, #-5
    ADD R0, R0, #-3
    STR R0, R5, #-5
    LDR R0, R5, #-5
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R1, R1, #0
    ADD R1, R1, #2
    LDR R0, R6, #0
    ADD R6, R6, #1
    AND R4, R4, #0
    ADD R3, R0, #0
    ADD R0, R0, #0
    BRzp mul_left_ok_15
    NOT R0, R0
    ADD R0, R0, #1
    ADD R4, R4, #1
mul_left_ok_15
    ADD R1, R1, #0
    BRzp mul_right_ok_16
    NOT R1, R1
    ADD R1, R1, #1
    ADD R4, R4, #1
mul_right_ok_16
    AND R2, R2, #0
    ADD R3, R0, #0
    BRz mul_done_18
mul_loop_17
    ADD R2, R2, R1
    ADD R3, R3, #-1
    BRp mul_loop_17
mul_done_18
    AND R4, R4, #1
    ADD R0, R2, #0
    ADD R4, R4, #0
    BRz sign_end_19
    NOT R0, R0
    ADD R0, R0, #1
sign_end_19
    STR R0, R5, #-5
    LDR R0, R5, #-5
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R1, R1, #0
    ADD R1, R1, #3
    LDR R0, R6, #0
    ADD R6, R6, #1
    AND R4, R4, #0
    ADD R3, R0, #0
    ADD R0, R0, #0
    BRzp mul_left_ok_20
    NOT R0, R0
    ADD R0, R0, #1
    ADD R4, R4, #1
mul_left_ok_20
    ADD R1, R1, #0
    BRzp mul_right_ok_21
    NOT R1, R1
    ADD R1, R1, #1
    ADD R4, R4, #1
mul_right_ok_21
    ADD R3, R0, #0
    AND R4, R4, #1
    ADD R0, R4, #0
    AND R2, R2, #0
    ADD R1, R1, #0
    BRz div_done_23
div_loop_22
    NOT R4, R1
    ADD R4, R4, #1
    ADD R4, R3, R4
    BRn div_done_23
    ADD R3, R4, #0
    ADD R2, R2, #1
    BRnzp div_loop_22
div_done_23
    ADD R0, R0, #0
    BRz sign_ok_24
    NOT R2, R2
    ADD R2, R2, #1
sign_ok_24
    ADD R0, R2, #0
    STR R0, R5, #-5
    LDR R0, R5, #-5
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R1, R1, #0
    ADD R1, R1, #5
    LDR R0, R6, #0
    ADD R6, R6, #1
    AND R4, R4, #0
    ADD R3, R0, #0
    ADD R0, R0, #0
    BRzp mul_left_ok_25
    NOT R0, R0
    ADD R0, R0, #1
    ADD R4, R4, #1
mul_left_ok_25
    ADD R1, R1, #0
    BRzp mul_right_ok_26
    NOT R1, R1
    ADD R1, R1, #1
    ADD R4, R4, #1
mul_right_ok_26
    ADD R3, R0, #0
    AND R4, R4, #1
    ADD R0, R4, #0
    AND R2, R2, #0
    ADD R1, R1, #0
    BRz div_done_28
div_loop_27
    NOT R4, R1
    ADD R4, R4, #1
    ADD R4, R3, R4
    BRn div_done_28
    ADD R3, R4, #0
    ADD R2, R2, #1
    BRnzp div_loop_27
div_done_28
    ADD R0, R0, #0
    BRz sign_ok_29
    NOT R3, R3
    ADD R3, R3, #1
sign_ok_29
    ADD R0, R3, #0
    STR R0, R5, #-5
    LDR R0, R5, #-5
    LEA R4, G_result
    STR R0, R4, #0
    AND R0, R0, #0
    LDR R1, R5, #-1
    LDR R4, R5, #-2
    LDR R3, R5, #-3
    LDR R2, R5, #-4
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
G_result .FILL #0
.END
