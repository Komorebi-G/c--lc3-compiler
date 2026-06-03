int result;

int value(int x) {
    return x;
}

int main() {
    int score = 0;

    if (value(2) && value(3)) {
        score += 1;
    }
    if (value(0) || value(4)) {
        score += 2;
    }
    if (!value(0) && !(value(5) == 0)) {
        score += 4;
    }

    result = score;
    return 0;
}
