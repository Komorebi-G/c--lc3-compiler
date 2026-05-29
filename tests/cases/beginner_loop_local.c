int main() {
    int i = 0;
    int acc = 0;
    while (i < 3) {
        int tmp = 0;
        tmp = tmp + i;
        acc = acc + tmp;
        i = i + 1;
    }
    putchar(acc + 48);
    putchar(10);
    return 0;
}
