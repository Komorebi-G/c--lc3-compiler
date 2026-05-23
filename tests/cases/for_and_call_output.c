int add(int a, int b) {
    return a + b;
}

int sum_to(int n) {
    int i = 0;
    int acc = 0;

    for (i = 0; i < n; i = i + 1) {
        acc = add(acc, i);
    }

    return acc;
}

int main() {
    int result = sum_to(4);
    putchar(result + 48);
    putchar(10);
    return 0;
}
