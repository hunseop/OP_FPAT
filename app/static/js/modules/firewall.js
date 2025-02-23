import { UI } from './ui.js';
import { Notification } from './notification.js';
import { Modal } from './modal.js';

export const Firewall = {
    initialize() {
        this.initializeSync();
        this.initializeSearch();
        this.initializeFilters();
        this.initializeStatusToggle();
        Modal.initializeEditButtons();
    },

    initializeSync() {
        document.querySelectorAll('.sync-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const row = btn.closest('tr');
                const firewallName = row.cells[1].textContent;
                const statusCell = row.querySelector('.sync-status');
                const originalText = statusCell.textContent;
                
                if (btn.disabled) {
                    Notification.addNotification('info', '동기화 진행 중', `${firewallName} 방화벽이 이미 동기화 중입니다.`);
                    return;
                }
                
                await this.startSync(id, firewallName, statusCell, btn, originalText);
            });
        });
    },

    initializeSearch() {
        const searchInput = document.getElementById('searchInput');
        const typeFilter = document.getElementById('typeFilter');
        if (!searchInput) return;

        let debounceTimer;

        const performSearch = () => {
            const searchTerm = searchInput.value.toLowerCase();
            const selectedType = typeFilter.value.toLowerCase();
            const tbody = document.getElementById('firewallTableBody');
            const rows = tbody.getElementsByTagName('tr');

            Array.from(rows).forEach(row => {
                const nameCell = row.cells[1];  // 이름 컬럼
                const typeCell = row.cells[2];  // 타입 컬럼
                const ipCell = row.cells[3];    // IP 컬럼
                
                const name = nameCell.textContent.toLowerCase();
                const type = typeCell.textContent.toLowerCase();
                const ip = ipCell.textContent.toLowerCase();

                const matchesSearch = name.includes(searchTerm) || 
                                    ip.includes(searchTerm);
                const matchesType = !selectedType || type.includes(selectedType);

                row.style.display = (matchesSearch && matchesType) ? '' : 'none';
            });
        };

        // 검색어 입력 시 디바운스 적용
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(performSearch, 300);
        });

        // 엔터 키 입력 시 즉시 검색
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                clearTimeout(debounceTimer);
                performSearch();
            }
        });

        // 검색창 클리어 버튼 클릭 시
        searchInput.addEventListener('search', performSearch);
    },

    initializeFilters() {
        const typeFilter = document.getElementById('typeFilter');
        if (!typeFilter) return;

        typeFilter.addEventListener('change', () => {
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                this.initializeSearch();
            }
        });
    },

    initializeStatusToggle() {
        document.querySelectorAll('.status-toggle').forEach(button => {
            button.addEventListener('click', async (e) => {
                const id = button.dataset.id;
                const isCurrentlyActive = button.classList.contains('active');
                const newStatus = !isCurrentlyActive;

                try {
                    const response = await fetch(`/api/firewall/status/${id}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ status: newStatus })
                    });

                    const data = await response.json();

                    if (data.success) {
                        button.classList.toggle('active');
                        button.classList.toggle('inactive');
                        button.textContent = newStatus ? '활성' : '비활성';
                        
                        Notification.addNotification(
                            'success',
                            '상태 변경 완료',
                            `방화벽 상태가 ${newStatus ? '활성' : '비활성'}으로 변경되었습니다.`
                        );
                    } else {
                        throw new Error(data.error);
                    }
                } catch (error) {
                    Notification.addNotification(
                        'error',
                        '상태 변경 실패',
                        error.message || '방화벽 상태 변경 중 오류가 발생했습니다.'
                    );
                }
            });
        });
    },

    async startSync(id, firewallName, statusCell, button, originalText) {
        try {
            button.disabled = true;
            button.classList.add('syncing');
            
            const response = await fetch(`/api/firewall/sync/${id}`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                statusCell.innerHTML = '<span class="sync-progress">동기화 중... <span class="progress-value">0</span>%</span>';
                this.checkProgress(id, firewallName, statusCell, button, originalText);
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            this.handleSyncError(firewallName, statusCell, button, originalText, error);
        }
    },

    async checkProgress(id, firewallName, statusCell, button, originalText) {
        try {
            const response = await fetch(`/api/firewall/sync/status/${id}`);
            const data = await response.json();

            if (data.status === 'success') {
                Notification.addNotification('success', '동기화 완료', `${firewallName} 방화벽 동기화가 완료되었습니다.`);
                button.disabled = false;
                button.classList.remove('syncing');
                setTimeout(() => location.reload(), 1000);
            } else if (data.status === 'syncing') {
                statusCell.querySelector('.progress-value').textContent = data.progress || 0;
                setTimeout(() => this.checkProgress(id, firewallName, statusCell, button, originalText), 1000);
            } else if (data.status === 'failed') {
                this.handleSyncError(firewallName, statusCell, button, originalText, data.error || '동기화 실패');
            }
        } catch (error) {
            this.handleSyncError(firewallName, statusCell, button, originalText, '상태 확인 중 오류가 발생했습니다.');
        }
    },

    handleSyncError(firewallName, statusCell, button, originalText, error) {
        Notification.addNotification('error', '동기화 실패', `${firewallName} 방화벽 동기화 중 오류가 발생했습니다: ${error}`);
        statusCell.innerHTML = `실패 <span class="error-tooltip" title="${error}">ⓘ</span>`;
        statusCell.className = 'sync-status failed';
        button.disabled = false;
        button.classList.remove('syncing');
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
    }
}; 