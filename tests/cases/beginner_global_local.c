int g;

int bump(int x) {
    return x + g;
}

int main() {
    g = 3;
    int v = bump(4);
    putchar(v + 48);
    putchar(10);
    return 0;
}
