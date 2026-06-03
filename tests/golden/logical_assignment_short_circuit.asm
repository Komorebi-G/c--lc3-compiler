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
    AND R0, R0, #0
    STR R0, R5, #-5
    STR R0, R5, #-6
    STR R0, R5, #-7
    AND R0, R0, #0
    STR R0, R5, #-5
    AND R0, R0, #0
    STR R0, R5, #-6
    AND R0, R0, #0
    STR R0, R5, #-7
    LDR R0, R5, #-5
    ADD R0, R0, #0
    BRz ifend_9
    AND R0, R0, #0
    ADD R0, R0, #1
    STR R0, R5, #-6
    ADD R0, R0, #0
    BRz ifend_9
    LD R0, LC_INT_0
    STR R0, R5, #-7
ifend_9
    LDR R0, R5, #-5
    ADD R0, R0, #0
    BRz or_skip_11
    AND R0, R0, #0
    ADD R0, R0, #2
    STR R0, R5, #-6
    ADD R0, R0, #0
    BRz ifend_10
or_skip_11
    LDR R0, R5, #-7
    ADD R0, R0, #1
    STR R0, R5, #-7
ifend_10
    AND R0, R0, #0
    ADD R0, R0, #1
    STR R0, R5, #-5
    ADD R0, R0, #0
    BRz ifend_12
    AND R0, R0, #0
    ADD R0, R0, #3
    STR R0, R5, #-6
    ADD R0, R0, #0
    BRz ifend_12
    LDR R0, R5, #-7
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-5
    ADD R6, R6, #-1
    STR R1, R6, #0
    LDR R2, R5, #-6
    LDR R1, R6, #0
    ADD R6, R6, #1
    ADD R1, R1, R2
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    STR R0, R5, #-7
ifend_12
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
    BRzp mul_left_ok_13
    NOT R0, R0
    ADD R0, R0, #1
    ADD R4, R4, #1
mul_left_ok_13
    ADD R1, R1, #0
    BRzp mul_right_ok_14
    NOT R1, R1
    ADD R1, R1, #1
    ADD R4, R4, #1
mul_right_ok_14
    AND R2, R2, #0
    ADD R3, R0, #0
    BRz mul_done_16
mul_loop_15
    ADD R2, R2, R1
    ADD R3, R3, #-1
    BRp mul_loop_15
mul_done_16
    AND R4, R4, #1
    ADD R0, R2, #0
    ADD R4, R4, #0
    BRz sign_end_17
    NOT R0, R0
    ADD R0, R0, #1
sign_end_17
    ADD R6, R6, #-1
    STR R0, R6, #0
    LDR R1, R5, #-6
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
LC_INT_0 .FILL #99
.END
