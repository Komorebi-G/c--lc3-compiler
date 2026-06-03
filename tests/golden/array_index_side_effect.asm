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
    AND R0, R0, #0
    STR R0, R5, #-6
    AND R0, R0, #0
    STR R0, R5, #-6
    LDR R1, R5, #-6
    ADD R2, R1, #0
    ADD R2, R2, #1
    STR R2, R5, #-6
    ADD R6, R6, #-1
    STR R1, R6, #0
    AND R0, R0, #0
    ADD R0, R0, #3
    LDR R1, R6, #0
    ADD R6, R6, #1
    ADD R2, R5, #-5
    ADD R2, R2, R1
    STR R0, R2, #0
    LDR R1, R5, #-6
    ADD R2, R1, #0
    ADD R2, R2, #1
    STR R2, R5, #-6
    ADD R6, R6, #-1
    STR R1, R6, #0
    AND R0, R0, #0
    ADD R0, R0, #4
    LDR R1, R6, #0
    ADD R6, R6, #1
    ADD R2, R5, #-5
    ADD R2, R2, R1
    STR R0, R2, #0
    LDR R1, R5, #-6
    ADD R1, R1, #1
    STR R1, R5, #-6
    ADD R6, R6, #-1
    STR R1, R6, #0
    AND R0, R0, #0
    ADD R0, R0, #5
    LDR R1, R6, #0
    ADD R6, R6, #1
    ADD R2, R5, #-5
    ADD R2, R2, R1
    STR R0, R2, #0
    AND R0, R0, #0
    ADD R1, R5, #-5
    ADD R1, R1, R0
    LDR R0, R1, #0
    ADD R6, R6, #-1
    STR R0, R6, #0
    LD R1, LC_INT_0
    LDR R0, R6, #0
    ADD R6, R6, #1
    AND R4, R4, #0
    ADD R3, R0, #0
    ADD R0, R0, #0
    BRzp mul_left_ok_10
    NOT R0, R0
    ADD R0, R0, #1
    ADD R4, R4, #1
mul_left_ok_10
    ADD R1, R1, #0
    BRzp mul_right_ok_11
    NOT R1, R1
    ADD R1, R1, #1
    ADD R4, R4, #1
mul_right_ok_11
    AND R2, R2, #0
    ADD R3, R0, #0
    BRz mul_done_13
mul_loop_12
    ADD R2, R2, R1
    ADD R3, R3, #-1
    BRp mul_loop_12
mul_done_13
    AND R4, R4, #1
    ADD R0, R2, #0
    ADD R4, R4, #0
    BRz sign_end_14
    NOT R0, R0
    ADD R0, R0, #1
sign_end_14
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R1, R1, #0
    ADD R1, R1, #1
    ADD R2, R5, #-5
    ADD R2, R2, R1
    LDR R1, R2, #0
    ADD R6, R6, #-1
    STR R1, R6, #0
    AND R2, R2, #0
    ADD R2, R2, #10
    LDR R1, R6, #0
    ADD R6, R6, #1
    AND R1, R1, #0
    ADD R1, R1, #1
    ADD R4, R5, #-5
    ADD R4, R4, R1
    LDR R1, R4, #0
    ADD R6, R6, #-1
    STR R1, R6, #0
    AND R1, R1, #0
    ADD R1, R1, #10
    ADD R6, R6, #-1
    STR R1, R6, #0
    LDR R2, R6, #1
    LDR R1, R6, #0
    ADD R6, R6, #2
    ADD R6, R6, #-1
    STR R1, R6, #0
    ADD R1, R2, #0
    LDR R3, R6, #0
    ADD R6, R6, #1
    AND R4, R4, #0
    ADD R2, R1, #0
    ADD R1, R1, #0
    BRzp mul_left_ok_15
    NOT R1, R1
    ADD R1, R1, #1
    ADD R4, R4, #1
mul_left_ok_15
    ADD R3, R3, #0
    BRzp mul_right_ok_16
    NOT R3, R3
    ADD R3, R3, #1
    ADD R4, R4, #1
mul_right_ok_16
    AND R0, R0, #0
    ADD R2, R1, #0
    BRz mul_done_18
mul_loop_17
    ADD R0, R0, R3
    ADD R2, R2, #-1
    BRp mul_loop_17
mul_done_18
    AND R4, R4, #1
    ADD R1, R0, #0
    ADD R4, R4, #0
    BRz sign_end_19
    NOT R1, R1
    ADD R1, R1, #1
sign_end_19
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R1, R1, #0
    ADD R1, R1, #3
    ADD R2, R5, #-5
    ADD R2, R2, R1
    LDR R1, R2, #0
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    LEA R4, G_result
    STR R0, R4, #0
    AND R0, R0, #0
    LDR R1, R5, #-1
    LDR R2, R5, #-2
    LDR R4, R5, #-3
    LDR R3, R5, #-4
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
G_result .FILL #0
LC_INT_0 .FILL #100
.END
