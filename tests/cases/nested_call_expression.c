int add(int a, int b) {
    return a + b;
}

int scale(int x, int factor) {
    return x * factor;
}

int main() {
    int value = scale(add(1, 2) + add(2, 3), 2);
    putchar(value / 10 + 48);
    putchar(value % 10 + 48);
    putchar(10);
    return 0;
}
