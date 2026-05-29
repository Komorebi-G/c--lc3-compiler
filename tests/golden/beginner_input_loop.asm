.ORIG x3000
main
    AND R0, R0, #0
    ST R0, ch
    AND R0, R0, #0
    ST R0, cnt

LOOP1
    GETC
    ST R0, ch

    LD R0, ch
    AND R1, R1, #0
    ADD R1, R1, #10
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRnp ENDIF3
    BRnzp DONE2
ENDIF3
    LD R0, cnt
    ADD R0, R0, #1
    ST R0, cnt
    BRnzp LOOP1
DONE2
    LD R0, cnt
    LD R1, ASCII_0
    ADD R0, R0, R1
    OUT
    AND R0, R0, #0
    ADD R0, R0, #10
    OUT
    AND R0, R0, #0
    HALT
ch .FILL #0
cnt .FILL #0
ASCII_0 .FILL #48
.END
