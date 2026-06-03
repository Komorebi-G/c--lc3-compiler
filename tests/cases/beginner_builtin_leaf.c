int emit_and_value(int x) {
    putchar(66);
    return x + 3;
}

int main() {
    int v = emit_and_value(3);
    putchar(v + 48);
    putchar(10);
    return 0;
}
