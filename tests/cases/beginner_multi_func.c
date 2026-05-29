int mul2(int a) {
    return a + a;
}

int sum3(int a, int b, int c) {
    return a + b + c;
}

int main() {
    int x = mul2(1);
    int y = sum3(1, 2, 3);
    putchar(x + y + 48);
    putchar(10);
    return 0;
}
