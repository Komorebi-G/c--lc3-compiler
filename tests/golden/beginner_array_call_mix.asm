.ORIG x3000
main
    AND R0, R0, #0
    ADD R0, R0, #1
    ST R0, values_0
    AND R0, R0, #0
    ADD R0, R0, #2
    ST R0, values_1
    AND R0, R0, #0
    ADD R0, R0, #3
    ST R0, values_2
    AND R0, R0, #0
    ST R0, i
    AND R0, R0, #0
    ST R0, sum

LOOP_1
    LD R0, i
    AND R1, R1, #0
    ADD R1, R1, #3
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRzp DONE_2
    LD R0, sum
    ST R0, add_a
    LD R0, i
    LEA R1, values_0
    ADD R1, R1, R0
    LDR R0, R1, #0
    ST R0, add_b
    JSR add_func
    ST R0, sum
    LD R0, i
    ADD R0, R0, #1
    ST R0, i
    BRnzp LOOP_1
DONE_2
    LD R0, sum
    LD R1, ASCII_0
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    HALT

add_func
    LD R0, add_a
    LD R1, add_b
    ADD R0, R0, R1
    RET

add_a .FILL #0
add_b .FILL #0
i .FILL #0
sum .FILL #0
values_0 .FILL #0
values_1 .FILL #0
values_2 .FILL #0
ASCII_0 .FILL #48
.END
