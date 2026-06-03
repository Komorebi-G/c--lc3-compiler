int result;

int pick(int x) {
    if (x < 0) {
        return 9;
    }
    if (x == 0) {
        return 4;
    }
    return x + 1;
}

int main() {
    result = pick(-1) + pick(0) + pick(1);
    return 0;
}
