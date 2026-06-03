int main() {
    char c = 65;
    bool ok = c == 65 && !0;
    if (ok) {
        putchar(c);
    }
    putchar(10);
    return 0;
}
