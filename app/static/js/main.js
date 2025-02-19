document.addEventListener('DOMContentLoaded', function() {
    // 현재 활성화된 메뉴 아이템 강조
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });

    // 알림 버튼 클릭 이벤트
    const notificationBtn = document.getElementById('notificationBtn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            // 알림 기능 구현
            console.log('알림 버튼 클릭됨');
        });
    }

    // 설정 버튼 클릭 이벤트
    const settingsBtn = document.getElementById('settingsBtn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            // 설정 기능 구현
            console.log('설정 버튼 클릭됨');
        });
    }

    // 사이드바 메뉴 아이템 호버 효과
    navItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
        });

        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });

    // 모달 관련 요소
    const modal = document.getElementById('firewallModal');
    const addBtn = document.getElementById('addFirewallBtn');
    const closeBtn = document.querySelector('.close-btn');
    const cancelBtn = document.getElementById('cancelBtn');
    const addCard = document.querySelector('.add-card');

    // 모달 열기
    function openModal() {
        modal.classList.add('active');
    }

    // 모달 닫기
    function closeModal() {
        modal.classList.remove('active');
        isEditMode = false;
        editingFirewallId = null;
        
        // 폼 초기화
        firewallForm.reset();
        // 모달 제목 원복
        document.querySelector('.modal-header h3').textContent = '방화벽 등록';
        // 버튼 텍스트 원복
        document.querySelector('#firewallForm button[type="submit"]').textContent = '등록';
    }

    // 이벤트 리스너
    if (addBtn) addBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    if (addCard) addCard.addEventListener('click', openModal);

    // 모달 외부 클릭시 닫기
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    // 에러 메시지 표시 함수
    function showError(message, details = []) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        
        let errorHtml = `<p class="error-main">${message}</p>`;
        if (details && details.length > 0) {
            errorHtml += '<ul class="error-details">';
            details.forEach(detail => {
                errorHtml += `<li>${detail}</li>`;
            });
            errorHtml += '</ul>';
        }
        
        errorDiv.innerHTML = errorHtml;
        
        // 이전 에러 메시지 제거
        const existingError = document.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        
        // 모달 내부에 에러 메시지 추가
        const modalBody = document.querySelector('.modal.active .modal-body');
        if (modalBody) {
            modalBody.insertBefore(errorDiv, modalBody.firstChild);
        }
        
        // 5초 후 자동으로 사라지게 설정
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    // 수정 모드 상태 변수
    let isEditMode = false;
    let editingFirewallId = null;

    // 수정 버튼 클릭
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.dataset.id;
            editingFirewallId = id;
            isEditMode = true;
            
            // 방화벽 데이터 가져오기
            fetch(`/firewall/edit/${id}`)
                .then(response => response.json())
                .then(data => {
                    // 폼 필드에 데이터 채우기
                    document.getElementById('name').value = data.name;
                    document.getElementById('type').value = data.type;
                    document.getElementById('ip').value = data.ip_address;
                    document.getElementById('username').value = data.username;
                    document.getElementById('password').value = '';  // 보안상 비밀번호는 비워둠
                    
                    // 모달 제목 변경
                    document.querySelector('.modal-header h3').textContent = '방화벽 수정';
                    // 버튼 텍스트 변경
                    document.querySelector('#firewallForm button[type="submit"]').textContent = '수정';
                    
                    // 모달 열기
                    openModal();
                });
        });
    });

    // 폼 제출 이벤트 수정
    const firewallForm = document.getElementById('firewallForm');
    if (firewallForm) {
        firewallForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            const url = isEditMode ? `/firewall/edit/${editingFirewallId}` : '/firewall/add';
            
            fetch(url, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    showError(data.error, data.details);
                }
            });
        });
    }

    // 동기화 버튼 클릭
    document.querySelectorAll('.sync-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.dataset.id;
            fetch(`/firewall/sync/${id}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                } else {
                    alert('동기화 실패: ' + data.error);
                }
            });
        });
    });

    // 삭제 버튼 클릭
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (confirm('정말 삭제하시겠습니까?')) {
                const id = this.dataset.id;
                fetch(`/firewall/delete/${id}`, {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('삭제 실패: ' + data.error);
                    }
                });
            }
        });
    });

    // 엑셀 업로드 모달 관련
    const uploadModal = document.getElementById('uploadModal');
    const uploadBtn = document.getElementById('uploadBtn');
    const cancelUploadBtn = document.getElementById('cancelUploadBtn');
    const uploadForm = document.getElementById('uploadForm');

    // 업로드 모달 열기
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function() {
            uploadModal.classList.add('active');
        });
    }

    // 업로드 모달 닫기
    if (cancelUploadBtn) {
        cancelUploadBtn.addEventListener('click', function() {
            uploadModal.classList.remove('active');
        });
    }

    // 파일 업로드 처리
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            
            fetch('/firewall/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.warnings && data.warnings.length > 0) {
                        showError('일부 데이터 처리 중 문제가 발생했습니다:', data.warnings);
                    }
                    if (data.message) {
                        alert(data.message);
                    }
                    if (!data.warnings || data.warnings.length === 0) {
                        location.reload();
                    }
                } else {
                    showError(data.error, data.details);
                }
            });
        });
    }

    // 방화벽 목록 검색 및 정렬 기능
    const searchInput = document.getElementById('searchInput');
    const typeFilter = document.getElementById('typeFilter');
    const sortField = document.getElementById('sortField');
    const sortOrder = document.getElementById('sortOrder');
    const firewallTableBody = document.getElementById('firewallTableBody');

    // 원본 데이터 저장
    let firewalls = [];
    if (firewallTableBody) {
        Array.from(firewallTableBody.getElementsByTagName('tr')).forEach(row => {
            firewalls.push({
                element: row,
                name: row.cells[0].textContent.toLowerCase(),
                type: row.cells[1].textContent.toLowerCase(),
                ip_address: row.cells[2].textContent.toLowerCase(),
                status: row.cells[3].textContent.trim() === '활성',
                last_sync: row.cells[4].textContent,
                policy_count: parseInt(row.cells[5].textContent) || 0
            });
        });
    }

    // 검색 및 필터링 함수
    function filterFirewalls() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedType = typeFilter.value.toLowerCase();
        const selectedField = sortField.value;
        const isAscending = sortOrder.value === 'asc';

        // 필터링
        let filteredFirewalls = firewalls.filter(firewall => {
            const matchesSearch = 
                firewall.name.includes(searchTerm) ||
                firewall.ip_address.includes(searchTerm);
            const matchesType = !selectedType || firewall.type === selectedType;
            return matchesSearch && matchesType;
        });

        // 정렬
        filteredFirewalls.sort((a, b) => {
            let comparison = 0;
            switch (selectedField) {
                case 'name':
                    comparison = a.name.localeCompare(b.name);
                    break;
                case 'type':
                    comparison = a.type.localeCompare(b.type);
                    break;
                case 'ip_address':
                    comparison = a.ip_address.localeCompare(b.ip_address);
                    break;
                case 'last_sync':
                    comparison = new Date(a.last_sync) - new Date(b.last_sync);
                    break;
                case 'policy_count':
                    comparison = a.policy_count - b.policy_count;
                    break;
            }
            return isAscending ? comparison : -comparison;
        });

        // 테이블 업데이트
        firewallTableBody.innerHTML = '';
        filteredFirewalls.forEach(firewall => {
            firewallTableBody.appendChild(firewall.element);
        });

        // 결과가 없을 경우 메시지 표시
        if (filteredFirewalls.length === 0) {
            const noResultsRow = document.createElement('tr');
            noResultsRow.innerHTML = '<td colspan="7" class="no-results">검색 결과가 없습니다.</td>';
            firewallTableBody.appendChild(noResultsRow);
        }
    }

    // 이벤트 리스너 등록
    if (searchInput) {
        searchInput.addEventListener('input', filterFirewalls);
    }
    if (typeFilter) {
        typeFilter.addEventListener('change', filterFirewalls);
    }
    if (sortField) {
        sortField.addEventListener('change', filterFirewalls);
    }
    if (sortOrder) {
        sortOrder.addEventListener('change', filterFirewalls);
    }

    // 테이블 헤더 클릭 시 정렬
    document.querySelectorAll('.firewall-table th[data-sort]').forEach(header => {
        header.addEventListener('click', function() {
            const field = this.dataset.sort;
            if (sortField.value === field) {
                // 같은 필드를 클릭한 경우 정렬 순서만 변경
                sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc';
            } else {
                // 다른 필드를 클릭한 경우 필드 변경
                sortField.value = field;
            }
            filterFirewalls();
            
            // 정렬 아이콘 업데이트
            document.querySelectorAll('.sort-icon').forEach(icon => {
                icon.textContent = '↕';
            });
            const icon = this.querySelector('.sort-icon');
            icon.textContent = sortOrder.value === 'asc' ? '↑' : '↓';
        });
    });
});
