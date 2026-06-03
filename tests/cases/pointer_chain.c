/* Chained pointer operations */
int main() {
    int a = 10;
    int b = 20;
    int p;
    int q;
    p = &a;
    q = &b;
    *p = *p + *q;  /* a = a + b = 30 */
    *q = *p - 5;   /* b = a - 5 = 25 */
    putchar(*p / 10 + 48);   /* '3' */
    putchar(*p % 10 + 48);   /* '0' */
    putchar(10);
    return 0;
}
