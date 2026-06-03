int main() {
    char ch = 65;
    char* p;

    p = &ch;
    *p += 1;

    putchar(ch);
    putchar(10);
    return 0;
}
