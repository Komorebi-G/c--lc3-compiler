.ORIG x3000
main
    AND R0, R0, #0
    ADD R0, R0, #3
    ST R0, emit_and_value_x
    JSR emit_and_value
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

emit_and_value
    ST R7, SAVE_R7_1
    LD R0, ASCII_B
    OUT
    LD R0, emit_and_value_x
    ADD R0, R0, #3
    LD R7, SAVE_R7_1
    RET

emit_and_value_x .FILL #0
v .FILL #0
SAVE_R7_1 .FILL #0
ASCII_0 .FILL #48
ASCII_B .FILL #66
.END
