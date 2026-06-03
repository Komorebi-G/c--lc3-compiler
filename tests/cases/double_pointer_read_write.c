int result;

int main() {
    int value = 6;
    int* p;
    int** q;

    p = &value;
    q = &p;
    **q = **q * 3;

    result = value + **q;
    return 0;
}
