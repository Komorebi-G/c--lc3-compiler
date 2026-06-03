int flag;

int side_one() {
    flag = flag + 1;
    return 1;
}

int side_zero() {
    flag = flag + 1;
    return 0;
}

int main() {
    flag = 0;
    if (side_one() && 0) {
        putchar(78);
    }
    putchar(flag + 48);
    if (side_zero() || 1) {
        putchar(flag + 48);
    }
    putchar(10);
    return 0;
}
