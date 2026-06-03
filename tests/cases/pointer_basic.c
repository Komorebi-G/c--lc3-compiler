int result;
int main() {
    int x = 42;
    int* p;
    p = &x;
    *p = 99;
    result = x;  /* 99 */
    return 0;
}
