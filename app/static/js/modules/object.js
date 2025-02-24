import { Notification } from './notification.js';

export const Object = {
    currentPage: 1,
    perPage: 50,
    sortBy: 'name',
    sortDesc: false,

    initialize() {
        this.initializeFilters();
        this.initializeSorting();
        this.initializePagination();
        this.loadObjects();

        // 검색 디바운스 설정
        let searchTimeout;
        document.getElementById('searchInput').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.currentPage = 1;
                this.loadObjects();
            }, 300);
        });
    },

    initializeFilters() {
        const typeFilter = document.getElementById('objectTypeFilter');
        const firewallFilter = document.getElementById('firewallFilter');

        typeFilter.addEventListener('change', () => {
            this.currentPage = 1;
            this.loadObjects();
        });

        firewallFilter.addEventListener('change', () => {
            this.currentPage = 1;
            this.loadObjects();
        });
    },

    initializeSorting() {
        document.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => {
                const column = th.dataset.sort;
                if (this.sortBy === column) {
                    this.sortDesc = !this.sortDesc;
                } else {
                    this.sortBy = column;
                    this.sortDesc = false;
                }
                this.loadObjects();
            });
        });
    },

    initializePagination() {
        document.getElementById('prevPage').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadObjects();
            }
        });

        document.getElementById('nextPage').addEventListener('click', () => {
            this.currentPage++;
            this.loadObjects();
        });

        document.getElementById('perPage').addEventListener('change', (e) => {
            this.perPage = parseInt(e.target.value);
            this.currentPage = 1;
            this.loadObjects();
        });
    },

    async loadObjects() {
        try {
            const searchTerm = document.getElementById('searchInput').value;
            const objectType = document.getElementById('objectTypeFilter').value;
            const firewallId = document.getElementById('firewallFilter').value;

            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                sort_by: this.sortBy,
                sort_desc: this.sortDesc,
                search: searchTerm,
                type: objectType,
                firewall_id: firewallId
            });

            const response = await fetch(`/api/object/list?${params}`);
            const data = await response.json();

            if (data.success) {
                this.renderObjects(data.data);
                this.updatePagination(data.data);
            }
        } catch (error) {
            console.error('객체 목록 로드 중 오류:', error);
            Notification.addNotification('error', '로드 실패', '객체 목록을 불러오는 중 오류가 발생했습니다.');
        }
    },

    renderObjects(data) {
        const tbody = document.getElementById('objectTableBody');
        tbody.innerHTML = data.objects.map(obj => `
            <tr>
                <td>${obj.name}</td>
                <td>
                    <span class="type-badge ${obj.type}">${this.getTypeDisplay(obj.type)}</span>
                </td>
                <td>${obj.firewall_name}</td>
                <td><code class="object-value">${this.formatValue(obj)}</code></td>
            </tr>
        `).join('');
    },

    updatePagination(data) {
        document.getElementById('currentPage').textContent = data.current_page;
        document.getElementById('totalPages').textContent = data.pages;
        document.getElementById('totalItems').textContent = data.total;
        
        document.getElementById('prevPage').disabled = data.current_page === 1;
        document.getElementById('nextPage').disabled = data.current_page === data.pages;
    },

    getTypeDisplay(type) {
        const typeMap = {
            'network': '네트워크',
            'network_group': '네트워크 그룹',
            'service': '서비스',
            'service_group': '서비스 그룹'
        };
        return typeMap[type] || type;
    },

    formatValue(obj) {
        if (obj.type === 'network') {
            return obj.value;
        } else if (obj.type === 'service') {
            return `${obj.protocol.toUpperCase()} ${obj.port}`;
        } else if (obj.type.endsWith('_group')) {
            return obj.members.join(', ');
        }
        return obj.value || '-';
    }
}; 