class ModalManager {
    constructor() {
        this.modal = document.getElementById('confirmModal');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // 취소 버튼 클릭
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.hide();
        });

        // 확인 버튼 클릭
        document.getElementById('confirmBtn').addEventListener('click', async () => {
            this.hide();
            await this.handleConfirm();
        });

        // ESC 키 누름
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hide();
            }
        });

        // 모달 외부 클릭
        window.onclick = (e) => {
            if (e.target === this.modal) {
                this.hide();
            }
        };
    }

    show() {
        this.modal.style.display = 'block';
    }

    hide() {
        this.modal.style.display = 'none';
    }

    async handleConfirm() {
        const card = document.querySelector('.card');
        card.classList.add('loading');

        try {
            const response = await fetch('/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(window.formManager.getFormData())
            });
            
            const result = await response.json();
            this.showResult(result);
        } catch (error) {
            this.showError(error);
        } finally {
            card.classList.remove('loading');
        }
    }

    showResult(result) {
        const resultDiv = document.getElementById('result');
        resultDiv.innerHTML = `
            <div class="alert alert-${result.status === 'success' ? 'success' : 'danger'}">
                <i class="fas fa-${result.status === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                ${result.message}
            </div>
        `;

        gsap.fromTo(resultDiv.querySelector('.alert'),
            { opacity: 0, y: 20 },
            { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }
        );
    }

    showError(error) {
        const resultDiv = document.getElementById('result');
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-circle"></i>
                Error: ${error.message}
            </div>
        `;

        gsap.fromTo(resultDiv.querySelector('.alert'),
            { opacity: 0, y: 20 },
            { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }
        );
    }
}

// DOM이 로드되면 ModalManager 인스턴스 생성
document.addEventListener('DOMContentLoaded', () => {
    window.modalManager = new ModalManager();
}); 