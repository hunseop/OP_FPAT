import { UI } from './ui.js';
import { Notification } from './notification.js';

export const Modal = {
    isEditMode: false,
    editingFirewallId: null,
    deleteData: {
        currentRow: null,
        currentId: null
    },
    filterCallback: null,

    initialize() {
        // 모달 관련 요소
        const modal = document.getElementById('firewallModal');
        const uploadModal = document.getElementById('uploadModal');
        const deleteModal = document.getElementById('deleteModal');
        const filterModal = document.getElementById('filterModal');
        const addBtn = document.getElementById('addFirewallBtn');
        const uploadBtn = document.getElementById('uploadBtn');
        const closeBtn = document.querySelector('#firewallModal .close-btn');
        const uploadCloseBtn = document.querySelector('#uploadModal .close-btn');
        const deleteCloseBtn = document.querySelector('#deleteModal .close-btn');
        const cancelBtn = document.getElementById('cancelBtn');
        const cancelUploadBtn = document.getElementById('cancelUploadBtn');
        const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        const addCard = document.querySelector('.add-card');
        const firewallForm = document.getElementById('firewallForm');
        const addFilterBtn = document.getElementById('addFilterBtn');

        // 필터 모달 요소
        if (filterModal) {
            const filterCloseBtn = filterModal.querySelector('.close-btn');
            const cancelFilterBtn = document.getElementById('cancelFilterBtn');
            const addFilterConditionBtn = document.getElementById('addFilterConditionBtn');
            const filterColumn = document.getElementById('filterColumn');

            // 필터 모달 이벤트
            if (addFilterBtn) {
                addFilterBtn.addEventListener('click', () => {
                    this.openModal(filterModal);
                    this.resetFilterModal();
                });
            }

            if (filterCloseBtn) {
                filterCloseBtn.addEventListener('click', () => {
                    this.closeModal(filterModal);
                });
            }

            if (cancelFilterBtn) {
                cancelFilterBtn.addEventListener('click', () => {
                    this.closeModal(filterModal);
                });
            }

            if (addFilterConditionBtn && filterColumn) {
                addFilterConditionBtn.addEventListener('click', () => {
                    this.handleFilterAdd();
                });

                filterColumn.addEventListener('change', () => {
                    this.handleFilterColumnChange();
                });
            }
        }

        // ESC 키 이벤트 등록
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const activeModal = document.querySelector('.modal.active');
                if (!activeModal) return;

                if (activeModal === modal) {
                    this.closeModal(modal, firewallForm);
                } else if (activeModal === uploadModal) {
                    this.closeModal(uploadModal);
                } else if (activeModal === deleteModal) {
                    this.closeDeleteModal();
                } else if (activeModal === filterModal) {
                    this.closeModal(filterModal);
                }
            }
        });

        // 이벤트 핸들러를 인스턴스 메서드로 바인딩
        this.boundHandleFormSubmit = this.handleFormSubmit.bind(this);

        // 이벤트 리스너 등록
        if (addBtn) addBtn.addEventListener('click', () => this.openModal(modal));
        if (uploadBtn) uploadBtn.addEventListener('click', () => this.openModal(uploadModal));
        if (closeBtn) closeBtn.addEventListener('click', () => this.closeModal(modal, firewallForm));
        if (uploadCloseBtn) uploadCloseBtn.addEventListener('click', () => this.closeModal(uploadModal));
        if (deleteCloseBtn) deleteCloseBtn.addEventListener('click', () => this.closeDeleteModal());
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.closeModal(modal, firewallForm));
        if (cancelUploadBtn) cancelUploadBtn.addEventListener('click', () => this.closeModal(uploadModal));
        if (cancelDeleteBtn) cancelDeleteBtn.addEventListener('click', () => this.closeDeleteModal());
        if (addCard) addCard.addEventListener('click', () => this.openModal(modal));

        // 삭제 확인 버튼 클릭
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => this.handleDelete());
        }

        // 모달 외부 클릭시 닫기
        window.addEventListener('click', (event) => {
            // 모달 컨텐츠가 아닌 배경을 클릭했을 때만 닫기
            if (event.target.classList.contains('modal')) {
                if (event.target === modal) {
                    this.closeModal(modal, firewallForm);
                } else if (event.target === uploadModal) {
                    this.closeModal(uploadModal);
                } else if (event.target === deleteModal) {
                    this.closeDeleteModal();
                } else if (event.target === filterModal) {
                    this.closeModal(filterModal);
                }
            }
        });

        // 폼 제출 이벤트 - 한 번만 등록
        if (firewallForm && !firewallForm.dataset.initialized) {
            firewallForm.addEventListener('submit', this.boundHandleFormSubmit);
            firewallForm.dataset.initialized = 'true';  // 초기화 표시
        }

        this.initializeEditButtons();
        this.initializeDeleteButtons();
    },

    openModal(modal) {
        modal.classList.add('active');
    },

    closeModal(modal, form) {
        modal.classList.remove('active');
        this.isEditMode = false;
        this.editingFirewallId = null;
        
        if (form) {
            form.reset();
            document.querySelector('.modal-header h3').textContent = '방화벽 등록';
            document.querySelector('#firewallForm button[type="submit"]').textContent = '등록';
        }
    },

    async handleFormSubmit(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const modal = document.getElementById('firewallModal');
        const submitButton = e.target.querySelector('button[type="submit"]');
        
        // 이미 제출 중인지 확인
        if (submitButton.disabled) {
            return;
        }
        
        // 제출 버튼 비활성화
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = '처리 중...';
        
        const formData = new FormData(e.target);
        
        try {
            const url = this.isEditMode ? 
                `/api/firewall/edit/${this.editingFirewallId}` : 
                '/api/firewall/add';
            
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const contentType = response.headers.get('content-type');
            let data;
            
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                throw new Error('서버 응답이 JSON 형식이 아닙니다.');
            }

            if (data.success) {
                // 성공 알림 표시
                Notification.addNotification(
                    'success',
                    this.isEditMode ? '방화벽 수정 완료' : '방화벽 등록 완료',
                    this.isEditMode ? '방화벽 정보가 수정되었습니다.' : '새로운 방화벽이 등록되었습니다.'
                );
                
                // 모달 닫기
                this.closeModal(modal, e.target);
                
                // 새로고침 전 처리
                Notification.beforeReload();
                location.reload();
            } else {
                throw new Error(data.error || '요청 처리 중 오류가 발생했습니다.');
            }
        } catch (error) {
            console.error('폼 제출 에러:', error);
            Notification.addNotification(
                'error',
                '요청 실패',
                error.message || '요청 처리 중 오류가 발생했습니다.'
            );
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    },

    initializeEditButtons() {
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                this.editingFirewallId = id;
                this.isEditMode = true;
                
                try {
                    const response = await fetch(`/api/firewall/edit/${id}`);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    
                    document.getElementById('name').value = data.name;
                    document.getElementById('type').value = data.type;
                    document.getElementById('ip').value = data.ip_address;
                    document.getElementById('username').value = data.username;
                    document.getElementById('password').value = '';
                    
                    document.querySelector('.modal-header h3').textContent = '방화벽 수정';
                    document.querySelector('#firewallForm button[type="submit"]').textContent = '수정';
                    
                    this.openModal(document.getElementById('firewallModal'));
                } catch (error) {
                    console.error('방화벽 정보 로드 에러:', error);
                    Notification.addNotification(
                        'error',
                        '정보 로드 실패',
                        '방화벽 정보를 불러오는 중 오류가 발생했습니다.'
                    );
                }
            });
        });
    },

    initializeDeleteButtons() {
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                const row = btn.closest('tr');
                const firewallName = row.cells[0].textContent;
                
                this.deleteData.currentId = id;
                this.deleteData.currentRow = row;
                
                document.getElementById('deleteFirewallName').textContent = firewallName;
                this.openModal(document.getElementById('deleteModal'));
            });
        });
    },

    closeDeleteModal() {
        const deleteModal = document.getElementById('deleteModal');
        this.closeModal(deleteModal);
        this.deleteData.currentRow = null;
        this.deleteData.currentId = null;
    },

    async handleDelete() {
        const { currentId, currentRow } = this.deleteData;
        if (!currentId || !currentRow) return;

        const firewallName = currentRow.cells[0].textContent;
        
        try {
            const response = await fetch(`/firewall/delete/${currentId}`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                Notification.addNotification('success', '삭제 완료', `${firewallName} 방화벽이 삭제되었습니다.`);
                currentRow.remove();
                this.closeDeleteModal();
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            Notification.addNotification(
                'error',
                '삭제 실패',
                error.message || '방화벽 삭제 중 오류가 발생했습니다.'
            );
        }
    },

    setFilterCallback(callback) {
        this.filterCallback = callback;
    },

    resetFilterModal() {
        const filterValueGroup = document.getElementById('filterValueGroup');
        const filterSelectGroup = document.getElementById('filterSelectGroup');
        const filterValue = document.getElementById('filterValue');
        const filterOperator = document.getElementById('filterOperator');
        const filterSelect = document.getElementById('filterSelect');

        if (filterValueGroup && filterSelectGroup && filterValue && filterOperator && filterSelect) {
            filterValueGroup.style.display = 'block';
            filterSelectGroup.style.display = 'none';
            filterValue.value = '';
            filterValue.placeholder = "필터 값 입력";
            filterOperator.disabled = false;
            filterSelect.value = '';
        }
    },

    handleFilterColumnChange() {
        const filterColumn = document.getElementById('filterColumn');
        const filterValueGroup = document.getElementById('filterValueGroup');
        const filterSelectGroup = document.getElementById('filterSelectGroup');
        const filterSelect = document.getElementById('filterSelect');
        const filterOperator = document.getElementById('filterOperator');

        if (!filterColumn || !filterValueGroup || !filterSelectGroup || !filterSelect || !filterOperator) return;

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
    },

    handleFilterAdd() {
        const filterColumn = document.getElementById('filterColumn');
        const filterOperator = document.getElementById('filterOperator');
        const filterValue = document.getElementById('filterValue');
        const filterSelect = document.getElementById('filterSelect');
        const filterModal = document.getElementById('filterModal');

        if (!filterColumn || !filterOperator || !filterValue || !filterSelect || !filterModal) return;

        const column = filterColumn.value;
        const operator = filterOperator.value;
        const value = column === 'enabled' || column === 'action' ? 
            filterSelect.value : filterValue.value;

        if (!value) {
            Notification.addNotification('error', '입력 오류', '필터 값을 입력해주세요.');
            return;
        }

        if (this.filterCallback) {
            this.filterCallback(column, operator, value);
        }

        this.closeModal(filterModal);
    }
}; 