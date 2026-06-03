int value() {
    return 9;
}

int main() {
    int x = 0;
    int* p;
    p = &x;
    *p = value();
    putchar(x + 48);
    putchar(10);
    return 0;
}
