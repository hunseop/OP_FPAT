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

    // 폼 제출
    const firewallForm = document.getElementById('firewallForm');
    if (firewallForm) {
        firewallForm.addEventListener('submit', function(e) {
            e.preventDefault();
            // TODO: 방화벽 등록 API 호출
            closeModal();
        });
    }
});
