int result;

int bump(int* p, int delta) {
    *p += delta;
    return *p;
}

int main() {
    int values[3] = {3, 7, 11};
    int* q;

    q = &values[1];
    result = bump(q, 5) + values[1];
    return 0;
}
