int seed() {
    return 5;
}

int main() {
    int values[3] = {1, seed(), 3};
    putchar(values[1] + 48);
    putchar(10);
    return 0;
}
