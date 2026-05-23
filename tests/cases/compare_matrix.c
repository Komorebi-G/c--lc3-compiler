int result;

int main() {
    int a = 3;
    int b = 5;
    int score = 0;

    if (a < b) {
        score = score + 1;
    }
    if (a <= 3) {
        score = score + 2;
    }
    if (b > a) {
        score = score + 4;
    }
    if (b >= 5) {
        score = score + 8;
    }
    if (a == 3) {
        score = score + 16;
    }
    if (a != b) {
        score = score + 32;
    }

    result = score;
    return 0;
}
