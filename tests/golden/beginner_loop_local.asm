.ORIG x3000
main
    AND R0, R0, #0
    ST R0, i
    AND R0, R0, #0
    ST R0, acc

LOOP1
    LD R0, i
    AND R1, R1, #0
    ADD R1, R1, #3
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRzp DONE2
    AND R0, R0, #0
    ST R0, tmp

    LD R0, tmp
    LD R1, i
    ADD R0, R0, R1
    ST R0, tmp
    LD R0, acc
    LD R1, tmp
    ADD R0, R0, R1
    ST R0, acc
    LD R0, i
    ADD R0, R0, #1
    ST R0, i
    BRnzp LOOP1
DONE2
    LD R0, acc
    LD R1, ASCII_0
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    HALT
acc .FILL #0
i .FILL #0
tmp .FILL #0
ASCII_0 .FILL #48
.END
