int main() {
    int i = 0;
    int sum = 0;

    for (; i < 6;) {
        i = i + 1;
        if (i == 3) {
            continue;
        }
        sum += i;
    }

    putchar(sum / 10 + 48);
    putchar(sum % 10 + 48);
    putchar(10);
    return 0;
}
