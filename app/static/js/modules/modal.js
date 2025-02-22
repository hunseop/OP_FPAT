import { UI } from './ui.js';

export const Modal = {
    isEditMode: false,
    editingFirewallId: null,

    initialize() {
        // 모달 관련 요소
        const modal = document.getElementById('firewallModal');
        const uploadModal = document.getElementById('uploadModal');
        const addBtn = document.getElementById('addFirewallBtn');
        const uploadBtn = document.getElementById('uploadBtn');
        const closeBtn = document.querySelector('#firewallModal .close-btn');
        const uploadCloseBtn = document.querySelector('#uploadModal .close-btn');
        const cancelBtn = document.getElementById('cancelBtn');
        const cancelUploadBtn = document.getElementById('cancelUploadBtn');
        const addCard = document.querySelector('.add-card');
        const firewallForm = document.getElementById('firewallForm');

        // 이벤트 핸들러를 인스턴스 메서드로 바인딩
        this.boundHandleFormSubmit = this.handleFormSubmit.bind(this);

        // 이벤트 리스너 등록
        if (addBtn) addBtn.addEventListener('click', () => this.openModal(modal));
        if (uploadBtn) uploadBtn.addEventListener('click', () => this.openModal(uploadModal));
        if (closeBtn) closeBtn.addEventListener('click', () => this.closeModal(modal, firewallForm));
        if (uploadCloseBtn) uploadCloseBtn.addEventListener('click', () => this.closeModal(uploadModal));
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.closeModal(modal, firewallForm));
        if (cancelUploadBtn) cancelUploadBtn.addEventListener('click', () => this.closeModal(uploadModal));
        if (addCard) addCard.addEventListener('click', () => this.openModal(modal));

        // 모달 외부 클릭시 닫기
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                this.closeModal(modal, firewallForm);
            }
            if (event.target === uploadModal) {
                this.closeModal(uploadModal);
            }
        });

        // 폼 제출 이벤트 - 한 번만 등록
        if (firewallForm && !firewallForm.dataset.initialized) {
            firewallForm.addEventListener('submit', this.boundHandleFormSubmit);
            firewallForm.dataset.initialized = 'true';  // 초기화 표시
        }

        this.initializeEditButtons();
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
        
        const url = this.isEditMode ? 
            `/firewall/edit/${this.editingFirewallId}` : 
            '/firewall/add';
        
        try {
            console.log('폼 제출 시작:', url);  // 디버깅용 로그
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            console.log('폼 제출 완료:', data);  // 디버깅용 로그

            if (data.success) {
                location.reload();
            } else {
                UI.showError(data.error, data.details);
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        } catch (error) {
            console.error('폼 제출 에러:', error);  // 디버깅용 로그
            UI.showError('요청 처리 중 오류가 발생했습니다.');
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
                    const response = await fetch(`/firewall/edit/${id}`);
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
                    UI.showError('방화벽 정보를 불러오는 중 오류가 발생했습니다.');
                }
            });
        });
    }
}; 