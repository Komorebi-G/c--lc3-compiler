int result;

int main() {
    int values[4];
    int i = 0;

    values[i++] = 3;
    values[i++] = 4;
    values[++i] = 5;

    result = values[0] * 100 + values[1] * 10 + values[3];
    return 0;
}
