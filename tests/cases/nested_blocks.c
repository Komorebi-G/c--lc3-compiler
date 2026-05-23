int result;

int main() {
    int x = 1;
    {
        int y = 4;
        x = x + y;
    }
    {
        int z = 3;
        x = x - z;
    }
    result = x;
    return 0;
}
