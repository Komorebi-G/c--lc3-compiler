int out;
int main() {
    int arr[10];
    int i = 2;
    int j = 4;
    /* complex index expressions */
    arr[i * 2] = 100;       /* arr[4] = 100 */
    arr[i + 3] = 25;        /* arr[5] = 25 */
    arr[j - 1] = 3;         /* arr[3] = 3 */
    arr[j / 2] = 40;        /* arr[2] = 40 */
    arr[j % 3] = 99;        /* arr[1] = 99 */
    out = arr[4] + arr[5] + arr[3] + arr[2] + arr[1];
    return 0;
}
