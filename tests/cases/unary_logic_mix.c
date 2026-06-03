int main() {
    int a = -5;
    int b = 0;

    putchar(48 + (-a == 5));
    putchar(48 + (!b));
    putchar(48 + (!(a + 5)));
    putchar(48 + (a < 0 && !b));
    putchar(10);
    return 0;
}
