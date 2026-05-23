int main() {
    int ch = 0;
    int count = 0;

    while (1) {
        ch = getchar();
        if (ch == 10) {
            break;
        }
        if (ch == 97) {
            count = count + 1;
        }
    }

    putchar(count + 48);
    putchar(10);
    return 0;
}
