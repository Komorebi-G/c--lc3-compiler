int emit_and_value(int x) {
    putchar(65);
    return x + 2;
}

int main() {
    int v = emit_and_value(5);
    putchar(v + 48);
    putchar(10);
    return 0;
}
