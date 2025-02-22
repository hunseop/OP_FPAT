// UI 관련 기능을 관리하는 모듈
export const UI = {
    initializeNavigation() {
        const currentPath = window.location.pathname;
        const navItems = document.querySelectorAll('.nav-item');
        
        navItems.forEach(item => {
            if (item.getAttribute('href') === currentPath) {
                item.classList.add('active');
            }
        });

        // 사이드바 메뉴 아이템 호버 효과
        navItems.forEach(item => {
            item.addEventListener('mouseenter', function() {
                this.style.transform = 'translateX(5px)';
            });

            item.addEventListener('mouseleave', function() {
                this.style.transform = 'translateX(0)';
            });
        });
    },

    showNotification(type, title, message, duration = 5000) {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        notification.innerHTML = `
            <div class="notification-content">
                <div class="notification-title">${title}</div>
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close">&times;</button>
        `;
        
        container.appendChild(notification);
        
        // 닫기 버튼 이벤트
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        });
        
        // 자동 제거
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);
        
        return notification;
    },

    showError(message, details = []) {
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
}; 