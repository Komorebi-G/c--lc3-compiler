/* Verify short-circuit evaluation with side effects */
int flag;
int side_effect() { flag = flag + 1; return 1; }
int main() {
    /* Test 1: a && b — if a is false, b should NOT be evaluated */
    flag = 0;
    if (0 && side_effect()) { putchar(78); }  /* 'N' if wrong */
    putchar(48 + flag);  /* should be '0' — side_effect not called */

    /* Test 2: 1 || b — if a is true, b should NOT be evaluated */
    flag = 0;
    if (1 || side_effect()) { putchar(48); }  /* just print '0' */
    putchar(48 + flag);  /* should be '0' — side_effect not called */
    putchar(10);
    return 0;
}
