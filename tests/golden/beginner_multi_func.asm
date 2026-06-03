.ORIG x3000
main
    AND R0, R0, #0
    ADD R0, R0, #1
    ST R0, mul2_a
    JSR mul2
    ST R0, x
    AND R0, R0, #0
    ADD R0, R0, #1
    ST R0, sum3_a
    AND R0, R0, #0
    ADD R0, R0, #2
    ST R0, sum3_b
    AND R0, R0, #0
    ADD R0, R0, #3
    ST R0, sum3_c
    JSR sum3
    ST R0, y

    LD R0, x
    LD R1, y
    ADD R0, R0, R1
    LD R1, ASCII_0
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    HALT

mul2
    LD R0, mul2_a
    LD R1, mul2_a
    ADD R0, R0, R1
    RET

sum3
    LD R0, sum3_a
    LD R1, sum3_b
    ADD R0, R0, R1
    LD R1, sum3_c
    ADD R0, R0, R1
    RET

x .FILL #0
y .FILL #0
mul2_a .FILL #0
sum3_a .FILL #0
sum3_b .FILL #0
sum3_c .FILL #0
ASCII_0 .FILL #48
.END
