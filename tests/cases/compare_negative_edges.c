int result;

int main() {
    int a = -2;
    int b = 3;
    int score = 0;

    if (a < b) {
        score += 1;
    }
    if (a <= -2) {
        score += 2;
    }
    if (b > a) {
        score += 4;
    }
    if (b >= 3) {
        score += 8;
    }
    if (a == -2) {
        score += 16;
    }
    if (a != b) {
        score += 32;
    }

    result = score;
    return 0;
}
