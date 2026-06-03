int next(int x) {
    return x + 1;
}

int main() {
    int i = 0;
    int sum = 0;

    for (i = 0; i < 4; i = next(i)) {
        if (i == 2) {
            continue;
        }
        sum = sum + i;
    }

    putchar(sum + 48);
    putchar(10);
    return 0;
}
