import { UI } from './modules/ui.js';
import { Firewall } from './modules/firewall.js';
import { Modal } from './modules/modal.js';
import { Notification } from './modules/notification.js';

document.addEventListener('DOMContentLoaded', function() {
    // UI 초기화
    UI.initializeNavigation();

    // 알림 시스템 초기화
    Notification.initialize();

    // 방화벽 관련 기능 초기화
    Firewall.initialize();

    // 모달 관련 기능 초기화
    Modal.initialize();

    // 알림 버튼 클릭 이벤트
    const notificationBtn = document.getElementById('notificationBtn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            console.log('알림 버튼 클릭됨');
        });
    }

    // 사이드바 메뉴 아이템 호버 효과
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        if (item.getAttribute('href') === window.location.pathname) {
            item.classList.add('active');
        }

        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px)';
        });

        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0)';
        });
    });
});
