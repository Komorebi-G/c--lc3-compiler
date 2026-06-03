int out;

int main() {
    int arr[4];
    int* p;
    int* q;

    arr[0] = 5;
    arr[1] = 7;
    arr[2] = 3;
    arr[3] = 4;

    p = &arr[2];
    *p = *p + 10;
    q = &arr[0];
    *q = arr[2] + arr[3];

    out = arr[0] + arr[2];
    return 0;
}
