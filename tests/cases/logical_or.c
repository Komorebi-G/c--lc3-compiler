int result;

int either(int x, int y) {
    if (x == 0 || y == 0)
        return 1;
    return 0;
}

int main() {
    int a = either(0, 5);   /* 0 == 0 true -> 1 (short-circuit) */
    int b = either(5, 0);   /* 5 == 0 false, 0 == 0 true -> 1 */
    int c = either(5, 5);   /* both non-zero -> 0 */
    result = a + b + c;     /* should be 1 + 1 + 0 = 2 */
    return 0;
}
