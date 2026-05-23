int result;

int main() {
    int i = 0;
    int sum = 0;

    while (i < 8) {
        i = i + 1;
        if (i == 2) {
            continue;
        }
        sum = sum + i;
        if (sum > 12) {
            break;
        }
    }

    result = sum;
    return 0;
}
