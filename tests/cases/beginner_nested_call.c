int add1(int x) {
    return x + 1;
}

int add2(int x) {
    return add1(add1(x));
}

int add4(int x) {
    return add2(add2(x));
}

int main() {
    int v = add4(1);
    putchar(v + 48);
    putchar(10);
    return 0;
}
