with open('index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_context(pattern, before=2, after=10):
    for i, l in enumerate(lines):
        if pattern in l:
            start = max(0, i - before)
            end = min(len(lines), i + after + 1)
            print(f'=== Pattern "{pattern}" at line {i+1} ===')
            for j in range(start, end):
                print(f'{j+1}: {lines[j].rstrip()}')
            print()
            break

print_context('(function () {', 1, 5)
print_context('function resolveApiBaseUrl()', 1, 30)
print_context('function getLiveStatusBadgeInfo()', 1, 20)
print_context('function applyDemoFallbackState(', 1, 25)
print_context('function initMap() {', 1, 25)
print_context('function renderDashboard() {', 1, 20)
print_context('function updateDashboardLiveView() {', 1, 35)
print_context('function updateDataSourceUI() {', 1, 35)
print_context('async function fetchLiveData(', 1, 30)
print_context('async function setDataSource(', 1, 25)
print_context('function initializeDataSource()', 1, 15)
print_context('function startPolling()', 1, 15)
