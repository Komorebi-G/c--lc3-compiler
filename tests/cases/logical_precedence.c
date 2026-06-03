int result;

/* Test that && has higher precedence than ||
   a || b && c  should parse as  a || (b && c) */
int main() {
    /* 0 || 1 && 0 -> 0 || (1 && 0) -> 0 || 0 -> 0 */
    int a = 0;
    int b = 1;
    int c = 0;
    if (a || b && c)
        result = 1;
    else
        result = 2;  /* should be 2 */

    return 0;
}
