/* Multiply edge cases: zero, one, negative, large */
int main() {
    int a =  0 * 5;      putchar(48 + (a == 0));   /* 1 */
    int b = -1 * 7;      putchar(48 + (b == -7));  /* 1 */
    int c = -3 * -6;     putchar(48 + (c == 18));  /* 1 */
    int d = 10 * 10;     putchar(48 + (d == 100)); /* 1 */
    putchar(10);
    return 0;
}
