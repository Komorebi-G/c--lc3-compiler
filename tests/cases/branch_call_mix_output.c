int inc(int x) {
    return x + 1;
}

int dec(int x) {
    return x - 1;
}

int main() {
    int value = 3;
    if (inc(value) == 4) {
        value = inc(value);
    } else {
        value = dec(value);
    }
    putchar(value + 48);
    putchar(10);
    return 0;
}
