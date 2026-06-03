int result;

int main() {
    int a = 0;
    int b = 0;
    int score = 0;

    if (a && (b = 1)) {
        score = 99;
    }
    if (!a || (b = 2)) {
        score += 1;
    }
    if ((a = 1) && (b = 3)) {
        score += a + b;
    }

    result = score * 10 + b;
    return 0;
}
