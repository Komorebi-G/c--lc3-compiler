.ORIG x3000
main
    AND R0, R0, #0
    ADD R0, R0, #1
    ST R0, add4_x
    ST R7, RET1
    JSR add4
    LD R7, RET1
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
    AND R1, R1, #0
    ADD R1, R1, #1
    ADD R0, R0, R1
    RET
add2
    LD R0, add2_x
    ST R0, add1_x
    ST R7, RET4
    JSR add1
    LD R7, RET4
    ST R0, add1_x
    ST R7, RET5
    JSR add1
    LD R7, RET5
    RET
add4
    LD R0, add4_x
    ST R0, add2_x
    ST R7, RET7
    JSR add2
    LD R7, RET7
    ST R0, add2_x
    ST R7, RET8
    JSR add2
    LD R7, RET8
    RET
add1_x .FILL #0
add2_x .FILL #0
add4_x .FILL #0
v .FILL #0
RET1 .FILL #0
RET4 .FILL #0
RET5 .FILL #0
RET7 .FILL #0
RET8 .FILL #0
ASCII_0 .FILL #48
.END
