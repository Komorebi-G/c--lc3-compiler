int result;
int main() {
    int a = 10;
    int *p;
    int **q;
    p = &a;
    q = &p;
    **q = 42;  /* a = 42 through double pointer */
    result = a;
    return 0;
}
