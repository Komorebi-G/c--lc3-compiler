/* Full operator precedence test */
int main() {
    /* && should bind tighter than || */
    int a = 0;
    int b = 1;
    int c = 0;
    /* a || b && c → 0 || (1 && 0) → 0 || 0 → 0 */
    if (a || b && c) { putchar(78); } else { putchar(89); }  /* 'Y' */

    /* * binds tighter than + */
    int d = 2 + 3 * 4;   /* 2 + 12 = 14 */
    putchar(48 + (d == 14));

    /* relational binds tighter than && */
    int e = 5;
    int f = 3;
    if (e > 0 && f < 0) { putchar(78); } else { putchar(89); }  /* 'Y' */

    /* = binds loosest */
    int g = 0;
    g = e > f;   /* g = 1 */
    putchar(48 + g);
    putchar(10);
    return 0;
}
