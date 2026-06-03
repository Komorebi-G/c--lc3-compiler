int result;

int main() {
    int values[5] = {2, 4};
    int i = 0;
    int sum = 0;

    while (i < 5) {
        sum += values[i];
        i++;
    }

    result = sum;
    return 0;
}
