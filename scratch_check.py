with open('index.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

def find_range(start_pat, end_pat):
    s = None
    for i, l in enumerate(lines):
        if start_pat in l and s is None:
            s = i
        if s is not None and end_pat in l and i > s:
            return s, i
    return s, None

print("resolveApiBaseUrl:", find_range("function resolveApiBaseUrl()", "const apiClient = {"))
print("apiClient:", find_range("const apiClient = {", "async checkHealth("))
print("renderDashboard:", find_range("function renderDashboard()", "function updateDashboardLiveView()"))
print("applyDemoFallbackState:", find_range("function applyDemoFallbackState(", "function activateFirmsUnavailable("))
print("initializeDataSource:", find_range("function initializeDataSource()", "function startPolling()"))
print("startPolling:", find_range("function startPolling()", "function initBackgroundServices()"))
