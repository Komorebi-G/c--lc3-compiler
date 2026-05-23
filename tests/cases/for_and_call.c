int result;
int limit = 5;

int add(int a, int b) {
    return a + b;
}

int sum_to(int n) {
    int i = 0;
    int acc = 0;

    for (i = 0; i < n; i = i + 1) {
        acc = add(acc, i);
    }

    return acc;
}

int main() {
    result = sum_to(limit);
    return 0;
}
