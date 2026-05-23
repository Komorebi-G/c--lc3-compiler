int main() {
    int ch;

    while (1) {
        ch = getchar();
        if (ch == 10) {
            break;
        }
        putchar(ch);
    }

    putchar(10);
    return 0;
}
