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
    LEA R0, LC_STR_0
    PUTS
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    LDR R7, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
LC_STR_0 .FILL #65
    .FILL #10
    .FILL #66
    .FILL #9
    .FILL #67
    .FILL #0
.END
