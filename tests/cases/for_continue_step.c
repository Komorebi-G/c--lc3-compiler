int main() {
    int i = 0;
    int sum = 0;

    for (i = 0; i < 5; i++) {
        if (i % 2 == 0) {
            continue;
        }
        sum = sum + i;
    }

    putchar(sum + 48);
    putchar(10);
    return 0;
}
