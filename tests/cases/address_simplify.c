int result;

int main() {
    int x = 3;
    int* p;

    p = &x;
    *&x = 7;
    *p = *&x + 2;

    result = x;
    return 0;
}
