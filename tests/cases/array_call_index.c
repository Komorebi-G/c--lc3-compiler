int pick() {
    return 2;
}

int main() {
    int values[4] = {1, 2, 3, 4};
    values[pick()] += 4;
    putchar(values[2] + 48);
    putchar(10);
    return 0;
}
