.ORIG x3000
    LD R6, STACK_TOP
    AND R5, R5, #0
    JSR main
    HALT
main
    LEA R0, LC_STR_0
    PUTS
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    LD R0, LC_INT_0
    OUT
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    RET
STACK_TOP .FILL xF000
LC_STR_0 .FILL #79
    .FILL #75
    .FILL #0
LC_INT_0 .FILL #65
.END
