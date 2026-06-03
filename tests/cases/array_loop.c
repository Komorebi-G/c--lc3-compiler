/* Array with loop: sum all elements */
int main() {
    int arr[5];
    int i = 0;
    while (i < 5) { arr[i] = i + 1; i = i + 1; }
    int sum = 0; i = 0;
    while (i < 5) { sum = sum + arr[i]; i = i + 1; }
    /* sum = 1+2+3+4+5 = 15 -> prints '1','5' */
    putchar(sum / 10 + 48);
    putchar(sum % 10 + 48);
    putchar(10);
    return 0;
}
