int add(int a, int b) {
    return a + b;
}

int main() {
    int values[3] = {1, 2, 3};
    int i = 0;
    int sum = 0;

    while (i < 3) {
        sum = add(sum, values[i]);
        i = i + 1;
    }

    putchar(sum + 48);
    putchar(10);
    return 0;
}
