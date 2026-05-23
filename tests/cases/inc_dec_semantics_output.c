int main() {
    int x = 3;
    int y = 0;

    y = x++;
    putchar(y + 48);
    putchar(x + 48);

    y = ++x;
    putchar(y + 48);
    putchar(x + 48);

    y = x--;
    putchar(y + 48);
    putchar(x + 48);

    y = --x;
    putchar(y + 48);
    putchar(x + 48);

    putchar(10);
    return 0;
}
