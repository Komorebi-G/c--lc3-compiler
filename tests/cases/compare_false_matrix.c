int result;

int main() {
    int a = 5;
    int b = 3;
    int score = 0;

    if (a < b) {
        score = 99;
    } else {
        score += 1;
    }
    if (a <= 4) {
        score = 99;
    } else {
        score += 2;
    }
    if (b > a) {
        score = 99;
    } else {
        score += 4;
    }
    if (b >= 5) {
        score = 99;
    } else {
        score += 8;
    }
    if (a == b) {
        score = 99;
    } else {
        score += 16;
    }
    if (a != 5) {
        score = 99;
    } else {
        score += 32;
    }

    result = score;
    return 0;
}
