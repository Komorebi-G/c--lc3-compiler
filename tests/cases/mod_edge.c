/* Modulo edge cases */
int main() {
    int a = 0 % 5;       putchar(48 + (a == 0));    /* 1 */
    int b = 7 % 1;       putchar(48 + (b == 0));    /* 1 */
    int c = 20 % 3;      putchar(48 + (c == 2));    /* 1 */
    int d = -20 % 3;     putchar(48 + (d == -2));   /* 1 */
    int e = 20 % -3;     putchar(48 + (e == 2));    /* 1 */
    int f = -20 % -3;    putchar(48 + (f == -2));   /* 1 */
    putchar(10);
    return 0;
}
