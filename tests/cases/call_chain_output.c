int add(int a, int b) {
    return a + b;
}

int twice(int x) {
    return add(x, x);
}

int bump3(int x) {
    return add(x, 3);
}

int main() {
    int value = bump3(twice(3));
    putchar(value + 48);
    putchar(10);
    return 0;
}
