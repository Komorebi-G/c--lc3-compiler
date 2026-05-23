int main() {
    int i = 0;
    int acc = 0;

    while (i < 5) {
        acc = acc + i;
        i = i + 1;
    }

    putchar(acc + 48);
    putchar(10);
    return 0;
}
