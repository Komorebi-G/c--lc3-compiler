int main() {
    int ch;
    int cnt = 0;
    while (1) {
        ch = getchar();
        if (ch == 10)
            break;
        cnt = cnt + 1;
    }
    putchar(cnt + 48);
    putchar(10);
    return 0;
}
