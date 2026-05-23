int result;

int add3(int a, int b, int c) {
    return a + b + c;
}

int mix(int x, int y, int z) {
    int t = add3(x, y, z);
    return t - y;
}

int main() {
    result = mix(4, 2, 3);
    return 0;
}
