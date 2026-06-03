int main() {
    int i = 0;
    int sum = 0;

    while (i < 4) {
        int j = 0;
        while (j < 4) {
            if (j == 1) {
                j = j + 1;
                continue;
            }
            if (i + j > 4) {
                break;
            }
            sum = sum + i + j;
            j = j + 1;
        }
        i = i + 1;
    }

    putchar(sum / 10 + 48);
    putchar(sum % 10 + 48);
    putchar(10);
    return 0;
}
