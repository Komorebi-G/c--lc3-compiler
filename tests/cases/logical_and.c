int result;

int check(int x) {
    if (x > 0 && x < 10)
        return 1;
    return 0;
}

int main() {
    int a = check(5);    /* 5 > 0 && 5 < 10 -> 1 */
    int b = check(0);    /* 0 > 0 -> 0 (short-circuit, don't eval 0 < 10) */
    int c = check(15);   /* 15 > 0 true, 15 < 10 false -> 0 */
    result = a + b + c;  /* should be 1 + 0 + 0 = 1 */
    return 0;
}
