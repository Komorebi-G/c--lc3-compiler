int main() {
    int i = 0;
    int sum = 0;

    for (i = 0; ; i = i + 1) {
        if (i == 5) {
            break;
        }
        sum = sum + i;
    }

    putchar(sum / 10 + 48);
    putchar(sum % 10 + 48);
    putchar(10);
    return 0;
}
