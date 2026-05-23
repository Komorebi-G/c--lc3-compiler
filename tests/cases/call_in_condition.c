int result;

int inc(int x) {
    return x + 1;
}

int main() {
    int value = 1;
    if (inc(value) == 2) {
        value = inc(value);
    } else {
        value = 9;
    }
    result = value;
    return 0;
}
