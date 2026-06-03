.ORIG x3000
main
    AND R0, R0, #0
    ADD R0, R0, #1
    ST R0, add4_x
    JSR add4
    ST R0, v

    LD R0, v
    LD R1, ASCII_0
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    HALT

add1
    LD R0, add1_x
    ADD R0, R0, #1
    RET

add2
    ST R7, SAVE_R7_1
    LD R0, add2_x
    ST R0, add1_x
    JSR add1
    ST R0, add1_x
    JSR add1
    LD R7, SAVE_R7_1
    RET

add4
    ST R7, SAVE_R7_2
    LD R0, add4_x
    ST R0, add2_x
    JSR add2
    ST R0, add2_x
    JSR add2
    LD R7, SAVE_R7_2
    RET

add1_x .FILL #0
add2_x .FILL #0
add4_x .FILL #0
v .FILL #0
SAVE_R7_1 .FILL #0
SAVE_R7_2 .FILL #0
ASCII_0 .FILL #48
.END
