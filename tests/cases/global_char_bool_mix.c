char marker = 65;
bool enabled = 1;
int result;

int main() {
    char offset = 2;
    bool disabled = 0;

    if (enabled && !disabled) {
        result = marker + offset;
    } else {
        result = 9;
    }

    return 0;
}
