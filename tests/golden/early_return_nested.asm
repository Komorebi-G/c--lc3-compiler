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
    ADD R6, R6, #-1
    STR R1, R6, #0
    ADD R6, R6, #-1
    STR R4, R6, #0
    AND R0, R0, #0
    ADD R0, R0, #-1
    ADD R6, R6, #-1
    STR R0, R6, #0
    JSR FN_pick
    ADD R6, R6, #1
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R0, R0, #0
    ADD R6, R6, #-1
    STR R0, R6, #0
    JSR FN_pick
    ADD R6, R6, #1
    ADD R1, R0, #0
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R0, R0, #0
    ADD R0, R0, #1
    ADD R6, R6, #-1
    STR R0, R6, #0
    JSR FN_pick
    ADD R6, R6, #1
    ADD R1, R0, #0
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
    LEA R4, G_result
    STR R0, R4, #0
    AND R0, R0, #0
    LDR R1, R5, #-1
    LDR R4, R5, #-2
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    LDR R7, R6, #0
    ADD R6, R6, #1
    RET
FN_pick
    ADD R6, R6, #-1
    STR R5, R6, #0
    ADD R5, R6, #0
    ADD R6, R6, #-1
    STR R1, R6, #0
    LDR R0, R5, #1
    AND R1, R1, #0
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRzp ifend_3
    AND R0, R0, #0
    ADD R0, R0, #9
    BRnzp pick_end_4
ifend_3
    LDR R0, R5, #1
    AND R1, R1, #0
    NOT R1, R1
    ADD R1, R1, #1
    ADD R1, R0, R1
    BRnp ifend_5
    AND R0, R0, #0
    ADD R0, R0, #4
    BRnzp pick_end_4
ifend_5
    LDR R0, R5, #1
    ADD R6, R6, #-1
    STR R0, R6, #0
    AND R1, R1, #0
    ADD R1, R1, #1
    LDR R0, R6, #0
    ADD R6, R6, #1
    ADD R0, R0, R1
pick_end_4
    LDR R1, R5, #-1
    ADD R6, R5, #0
    LDR R5, R6, #0
    ADD R6, R6, #1
    RET
STACK_TOP .FILL xF000
G_result .FILL #0
.END
