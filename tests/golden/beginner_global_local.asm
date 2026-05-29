.ORIG x3000
main
    AND R0, R0, #0
    ADD R0, R0, #3
    ST R0, G_g
    AND R0, R0, #0
    ADD R0, R0, #4
    ST R0, bump_x
    ST R7, RET1
    JSR bump
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
bump
    LD R0, bump_x
    LD R1, G_g
    ADD R0, R0, R1
    RET
G_g .FILL #0
bump_x .FILL #0
v .FILL #0
RET1 .FILL #0
ASCII_0 .FILL #48
.END
