int result;
int main() {
    int x = 42;
    int* p;
    char c = 65;
    bool b = 1;
    p = &x;
    *p = *p + c;  /* 42 + 65 = 107 */
    result = x;
    return 0;
}
