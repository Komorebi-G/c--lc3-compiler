int out;

int main() {
    int x = 20;
    int* p;

    p = &x;
    *p += 5;
    *p /= 3;
    *p *= 4;
    *p %= 7;

    out = x;
    return 0;
}
