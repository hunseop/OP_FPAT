import { Notification } from './notification.js';

export const Policy = {
    filters: [],
    currentPage: 1,
    perPage: 50,
    sortBy: 'seq',
    sortDesc: false,

    initialize() {
        this.loadStateFromStorage();
        this.initializeFilters();
        this.initializeSorting();
        this.initializePagination();
        this.initializeExport();
        this.loadPolicies();

        // 페이지 언로드 시 상태 저장
        window.addEventListener('beforeunload', () => {
            this.saveStateToStorage();
        });
    },

    loadStateFromStorage() {
        const savedState = localStorage.getItem('policyState');
        if (savedState) {
            const state = JSON.parse(savedState);
            this.filters = state.filters || [];
            this.currentPage = state.currentPage || 1;
            this.perPage = state.perPage || 50;
            this.sortBy = state.sortBy || 'seq';
            this.sortDesc = state.sortDesc || false;
        }
    },

    saveStateToStorage() {
        const state = {
            filters: this.filters,
            currentPage: this.currentPage,
            perPage: this.perPage,
            sortBy: this.sortBy,
            sortDesc: this.sortDesc
        };
        localStorage.setItem('policyState', JSON.stringify(state));
    },

    initializeFilters() {
        const addFilterBtn = document.getElementById('addFilterBtn');
        const resetFilterBtn = document.getElementById('resetFilterBtn');
        const filterModal = document.getElementById('filterModal');
        const closeBtn = filterModal.querySelector('.close-btn');
        const cancelFilterBtn = document.getElementById('cancelFilterBtn');
        const addFilterConditionBtn = document.getElementById('addFilterConditionBtn');
        const filterColumn = document.getElementById('filterColumn');
        const filterOperator = document.getElementById('filterOperator');
        const filterValueGroup = document.getElementById('filterValueGroup');
        const filterSelectGroup = document.getElementById('filterSelectGroup');
        const filterValue = document.getElementById('filterValue');
        const filterSelect = document.getElementById('filterSelect');

        // 필터 모달 이벤트
        addFilterBtn.addEventListener('click', () => {
            filterModal.classList.add('active');
            this.resetFilterModal(filterValueGroup, filterSelectGroup, filterValue);
        });

        closeBtn.addEventListener('click', () => {
            filterModal.classList.remove('active');
        });

        cancelFilterBtn.addEventListener('click', () => {
            filterModal.classList.remove('active');
        });

        // 필터 초기화 버튼 이벤트
        resetFilterBtn.addEventListener('click', () => {
            this.filters = [];
            this.currentPage = 1;
            this.updateFilterDisplay();
            this.loadPolicies();
        });

        // 필터 컬럼 변경 이벤트
        filterColumn.addEventListener('change', () => {
            const column = filterColumn.value;
            if (column === 'enabled') {
                filterValueGroup.style.display = 'none';
                filterSelectGroup.style.display = 'block';
                filterSelect.innerHTML = `
                    <option value="">선택하세요</option>
                    <option value="활성">활성</option>
                    <option value="비활성">비활성</option>
                `;
                filterOperator.value = 'equals';
                filterOperator.disabled = true;
            } else if (column === 'action') {
                filterValueGroup.style.display = 'none';
                filterSelectGroup.style.display = 'block';
                filterSelect.innerHTML = `
                    <option value="">선택하세요</option>
                    <option value="허용">허용</option>
                    <option value="차단">차단</option>
                `;
                filterOperator.value = 'equals';
                filterOperator.disabled = true;
            } else {
                filterValueGroup.style.display = 'block';
                filterSelectGroup.style.display = 'none';
                filterOperator.disabled = false;
            }
        });

        // 필터 추가 버튼 이벤트
        addFilterConditionBtn.addEventListener('click', () => {
            const column = filterColumn.value;
            const operator = filterOperator.value;
            const value = column === 'enabled' || column === 'action' ? 
                filterSelect.value : filterValue.value;

            if (!value) {
                alert('필터 값을 입력해주세요.');
                return;
            }

            this.addFilter(column, operator, value);
            filterModal.classList.remove('active');
        });

        // 초기 필터 표시
        this.updateFilterDisplay();
    },

    resetFilterModal(filterValueGroup, filterSelectGroup, filterValue) {
        filterValueGroup.style.display = 'block';
        filterSelectGroup.style.display = 'none';
        filterValue.value = '';
        filterValue.placeholder = "필터 값 입력";
        document.getElementById('filterOperator').disabled = false;
        document.getElementById('filterSelect').value = '';
    },

    addFilter(column, operator, value) {
        const columnNames = {
            'firewall_name': '방화벽',
            'name': '이름',
            'enabled': '상태',
            'action': '동작',
            'source': '출발지',
            'user': '사용자',
            'destination': '목적지',
            'service': '서비스',
            'application': '애플리케이션',
            'security_profile': '보안 프로필',
            'category': '카테고리'
        };

        const operatorNames = {
            'contains': '포함',
            'equals': '일치',
            'starts': '시작',
            'ends': '끝'
        };

        this.filters.push({ column, operator, value });
        this.updateFilterDisplay();
        this.loadPolicies();
    },

    removeFilter(index) {
        this.filters.splice(index, 1);
        this.updateFilterDisplay();
        this.loadPolicies();
    },

    updateFilterDisplay() {
        const filterList = document.getElementById('filterList');
        const filterEmpty = filterList.querySelector('.filter-empty');
        
        // 기존 필터 항목 제거 (empty 메시지 제외)
        Array.from(filterList.children)
            .filter(child => !child.classList.contains('filter-empty'))
            .forEach(child => child.remove());

        if (this.filters.length === 0) {
            filterEmpty.style.display = 'block';
            return;
        }

        filterEmpty.style.display = 'none';
        
        // 필터 항목 추가
        this.filters.forEach((filter, index) => {
            const filterItem = document.createElement('div');
            filterItem.className = 'filter-item';
            
            const columnName = document.querySelector(`#filterColumn option[value="${filter.column}"]`).textContent;
            const operatorName = document.querySelector(`#filterOperator option[value="${filter.operator}"]`).textContent;
            
            filterItem.innerHTML = `
                <span>${columnName} ${operatorName} ${filter.value}</span>
                <button class="remove-filter" data-index="${index}">&times;</button>
            `;
            
            filterItem.querySelector('.remove-filter').addEventListener('click', () => {
                this.removeFilter(index);
            });
            
            filterList.appendChild(filterItem);
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
                this.loadPolicies();
            });
        });
    },

    initializePagination() {
        document.getElementById('prevPage').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.loadPolicies();
            }
        });

        document.getElementById('nextPage').addEventListener('click', () => {
            this.currentPage++;
            this.loadPolicies();
        });

        document.getElementById('perPage').addEventListener('change', (e) => {
            this.perPage = parseInt(e.target.value);
            this.currentPage = 1;
            this.loadPolicies();
        });
    },

    initializeExport() {
        document.getElementById('exportBtn').addEventListener('click', () => {
            this.exportPolicies();
        });
    },

    async loadPolicies() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                per_page: this.perPage,
                sort_by: this.sortBy,
                sort_desc: this.sortDesc
            });

            // 필터 조건 추가
            this.filters.forEach((filter, index) => {
                params.append(`filters[${index}][column]`, filter.column);
                params.append(`filters[${index}][operator]`, filter.operator);
                params.append(`filters[${index}][value]`, filter.value);
            });

            const response = await fetch(`/api/policy/list?${params}`);
            const data = await response.json();

            if (data.success) {
                this.renderPolicies(data);
                this.updatePagination(data);
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('정책 로드 중 오류:', error);
        }
    },

    renderPolicies(data) {
        const tbody = document.getElementById('policyTableBody');
        tbody.innerHTML = data.data.policies.map(policy => `
            <tr>
                <td>${policy.firewall_name}</td>
                <td>${policy.seq}</td>
                <td>${policy.name}</td>
                <td><span class="badge ${policy.enabled === '활성' ? 'active' : 'inactive'}">${policy.enabled}</span></td>
                <td>${policy.action}</td>
                <td>${policy.source || '-'}</td>
                <td>${policy.user || '-'}</td>
                <td>${policy.destination || '-'}</td>
                <td>${policy.service || '-'}</td>
                <td>${policy.application || '-'}</td>
                <td>${policy.security_profile || '-'}</td>
                <td>${policy.category || '-'}</td>
                <td>${policy.last_hit || '-'}</td>
                <td>${policy.description || '-'}</td>
            </tr>
        `).join('');
    },

    updatePagination(data) {
        document.getElementById('currentPage').textContent = data.data.current_page;
        document.getElementById('totalPages').textContent = data.data.pages;
        document.getElementById('totalItems').textContent = data.data.total;
        
        document.getElementById('prevPage').disabled = data.data.current_page === 1;
        document.getElementById('nextPage').disabled = data.data.current_page === data.data.pages;
    },

    async exportPolicies() {
        try {
            const params = new URLSearchParams();
            
            // 필터 조건 추가
            this.filters.forEach((filter, index) => {
                params.append(`filters[${index}][column]`, filter.column);
                params.append(`filters[${index}][operator]`, filter.operator);
                params.append(`filters[${index}][value]`, filter.value);
            });

            const response = await fetch(`/api/policy/export?${params}`);
            if (!response.ok) throw new Error('Export failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `policies_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('정책 내보내기 중 오류:', error);
        }
    }
}; 