import { UI } from './ui.js';
import { Notification } from './notification.js';

export const Firewall = {
    initializeSync() {
        document.querySelectorAll('.sync-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = this.dataset.id;
                const originalText = this.textContent;
                const statusCell = this.closest('tr').querySelector('.sync-status');
                const firewallName = this.closest('tr').cells[0].textContent;
                
                if (this.disabled) {
                    Notification.addNotification('info', '동기화 진행 중', `${firewallName} 방화벽이 이미 동기화 중입니다.`);
                    return;
                }
                
                this.disabled = true;
                this.classList.add('syncing');
                
                statusCell.innerHTML = '<span class="sync-progress">동기화 중... <span class="progress-value">0</span>%</span>';
                statusCell.className = 'sync-status syncing';
                
                Notification.addNotification('info', '동기화 시작', `${firewallName} 방화벽 동기화를 시작합니다.`);
                
                this.startSync(id, firewallName, statusCell, this, originalText);
            });
        });
    },

    initialize() {
        this.initializeSync();
        this.initializeTableSort();
        this.initializeSearch();
        this.initializeFilters();
    },

    initializeTableSort() {
        const table = document.querySelector('.firewall-table');
        if (!table) return;

        const headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.dataset.sort;
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                const isAsc = header.classList.contains('asc');

                // 정렬 방향 표시 업데이트
                headers.forEach(h => h.classList.remove('asc', 'desc'));
                header.classList.toggle(isAsc ? 'desc' : 'asc');

                // 데이터 정렬
                rows.sort((a, b) => {
                    const aValue = a.querySelector(`td:nth-child(${this._getColumnIndex(column)})`).textContent;
                    const bValue = b.querySelector(`td:nth-child(${this._getColumnIndex(column)})`).textContent;
                    return isAsc ? bValue.localeCompare(aValue) : aValue.localeCompare(bValue);
                });

                // 정렬된 행 다시 삽입
                tbody.innerHTML = '';
                rows.forEach(row => tbody.appendChild(row));
            });
        });
    },

    initializeSearch() {
        const searchInput = document.getElementById('searchInput');
        if (!searchInput) return;

        searchInput.addEventListener('input', () => {
            const searchTerm = searchInput.value.toLowerCase();
            const rows = document.querySelectorAll('#firewallTableBody tr');

            rows.forEach(row => {
                const name = row.cells[0].textContent.toLowerCase();
                const ip = row.cells[2].textContent.toLowerCase();
                const matches = name.includes(searchTerm) || ip.includes(searchTerm);
                row.style.display = matches ? '' : 'none';
            });
        });
    },

    initializeFilters() {
        const typeFilter = document.getElementById('typeFilter');
        if (!typeFilter) return;

        typeFilter.addEventListener('change', () => {
            const selectedType = typeFilter.value.toLowerCase();
            const rows = document.querySelectorAll('#firewallTableBody tr');

            rows.forEach(row => {
                const type = row.cells[1].textContent.toLowerCase();
                row.style.display = !selectedType || type === selectedType ? '' : 'none';
            });
        });
    },

    _getColumnIndex(column) {
        const columnMap = {
            'name': 1,
            'type': 2,
            'ip_address': 3,
            'last_sync': 5,
            'policy_count': 6
        };
        return columnMap[column] || 1;
    },

    async startSync(id, firewallName, statusCell, button, originalText) {
        try {
            const response = await fetch(`/api/firewall/sync/${id}`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                this.checkProgress(id, firewallName, statusCell, button, originalText);
            } else {
                this.handleSyncError(firewallName, statusCell, button, originalText, data.error);
            }
        } catch (error) {
            this.handleSyncError(firewallName, statusCell, button, originalText, '동기화 요청 중 오류가 발생했습니다.');
        }
    },

    async checkProgress(id, firewallName, statusCell, button, originalText) {
        try {
            const response = await fetch(`/api/firewall/sync/status/${id}`);
            const data = await response.json();

            if (data.success) {
                Notification.addNotification('success', '동기화 완료', `${firewallName} 방화벽 동기화가 완료되었습니다.`);
                statusCell.innerHTML = data.last_sync;
                statusCell.className = 'sync-status';
                button.disabled = false;
                button.classList.remove('syncing');
                button.textContent = originalText;
                setTimeout(() => location.reload(), 1000);
            } else if (data.status === 'syncing') {
                statusCell.querySelector('.progress-value').textContent = data.progress || 0;
                setTimeout(() => this.checkProgress(id, firewallName, statusCell, button, originalText), 1000);
            } else {
                this.handleSyncError(firewallName, statusCell, button, originalText, data.error);
            }
        } catch (error) {
            this.handleSyncError(firewallName, statusCell, button, originalText, '상태 확인 중 오류가 발생했습니다.');
        }
    },

    handleSyncError(firewallName, statusCell, button, originalText, error) {
        Notification.addNotification('error', '동기화 실패', `${firewallName} 방화벽 동기화 중 오류가 발생했습니다: ${error}`);
        statusCell.innerHTML = '실패';
        statusCell.className = 'sync-status failed';
        button.disabled = false;
        button.classList.remove('syncing');
        button.textContent = originalText;
    }
}; 