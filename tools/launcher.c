/*
 * Q1 Browser Windows launcher.
 *
 * Small native launcher that finds its own directory, points the embedded
 * Windows Python at the app and Qt folders, then starts runtime\pythonw.exe.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <wchar.h>

static void my_get_exe_dir(WCHAR *out, DWORD size)
{
    DWORD n = GetModuleFileNameW(NULL, out, size);
    if (n > 0) {
        for (DWORD i = n; i > 0; i--) {
            if (out[i - 1] == L'\\' || out[i - 1] == L'/') {
                out[i - 1] = L'\0';
                return;
            }
        }
    }
    wcscpy(out, L".");
}

int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance,
                    LPWSTR lpCmdLine, int nCmdShow)
{
    (void)hInstance;
    (void)hPrevInstance;
    (void)lpCmdLine;
    (void)nCmdShow;

    WCHAR exe_dir[MAX_PATH];
    my_get_exe_dir(exe_dir, MAX_PATH);

    WCHAR runtime[MAX_PATH];
    WCHAR app[MAX_PATH];
    WCHAR pythonw[MAX_PATH];
    WCHAR cmdline[4096];
    WCHAR pyhome[4096];
    WCHAR sitepkgs[MAX_PATH];
    WCHAR qtbin[MAX_PATH];
    WCHAR base_path[32768];
    WCHAR full_path[65536];

    swprintf(runtime, MAX_PATH, L"%s\\runtime", exe_dir);
    swprintf(app, MAX_PATH, L"%s\\app", exe_dir);
    swprintf(pythonw, MAX_PATH, L"%s\\pythonw.exe", runtime);
    swprintf(cmdline, 4096, L"\"%s\" \"%s\\run.py\"", pythonw, app);
    swprintf(pyhome, 4096, L"%s", runtime);
    swprintf(sitepkgs, MAX_PATH, L"%s\\Lib\\site-packages", runtime);
    swprintf(qtbin, MAX_PATH,
             L"%s\\PyQt6\\Qt6\\bin", sitepkgs);

    DWORD plen = GetEnvironmentVariableW(L"PATH", base_path, 32768);
    if (plen == 0 || plen >= 32768) {
        wcscpy(base_path, L"C:\\Windows\\System32;C:\\Windows");
    }

    swprintf(full_path, 65536, L"%s;%s;%s;%s", runtime, sitepkgs, qtbin, base_path);
    SetEnvironmentVariableW(L"PATH", full_path);
    SetEnvironmentVariableW(L"PYTHONHOME", runtime);
    SetEnvironmentVariableW(L"Q1_EXE_DIR", exe_dir);

    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    ZeroMemory(&pi, sizeof(pi));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_SHOWNORMAL;

    BOOL ok = CreateProcessW(NULL, cmdline, NULL, NULL, FALSE,
                             CREATE_UNICODE_ENVIRONMENT, NULL, exe_dir,
                             &si, &pi);
    if (ok) {
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
        return 0;
    }

    WCHAR msg[2048];
    wsprintfW(msg, L"Q1 Browser could not start.\n\n%lu\n\n%s",
              (unsigned long)GetLastError(), cmdline);
    MessageBoxW(NULL, msg, L"Q1 Browser", MB_OK | MB_ICONERROR);
    return 1;
}
