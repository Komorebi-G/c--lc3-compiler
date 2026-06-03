int result;

int store(int value) {
    result = value;
    return;
}

int main() {
    store(11);
    result += 1;
    return 0;
}
