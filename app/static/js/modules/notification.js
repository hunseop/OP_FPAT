export const Notification = {
    notifications: [],
    container: null,
    timers: new Map(), // 타이머 관리를 위한 Map 추가

    initialize() {
        // 기존에 생성된 알림 컨테이너들을 모두 제거
        document.querySelectorAll('.notification-container:not(#notificationContainer)').forEach(el => el.remove());
        
        this.container = document.getElementById('notificationContainer');
        if (!this.container) {
            console.error('알림 컨테이너를 찾을 수 없습니다.');
            return;
        }

        // 알림 드롭다운 초기화
        this.initializeDropdown();
        
        // 초기 알림 로드
        this.loadNotifications();
        
        // 주기적으로 새 알림 확인
        setInterval(() => this.checkNewNotifications(), 30000);

        // 전역 이벤트 리스너 등록
        window.Notification = {
            removeNotification: (id) => this.removeNotification(id)
        };
    },

    initializeDropdown() {
        const notificationBtn = document.getElementById('notificationBtn');
        const notificationMenu = document.querySelector('.notification-menu');
        const clearAllBtn = document.querySelector('.clear-all');
        const notificationBadge = document.querySelector('.notification-badge');

        if (notificationBtn && notificationMenu) {
            notificationBtn.addEventListener('click', () => {
                notificationMenu.classList.toggle('active');
            });

            // 외부 클릭 시 메뉴 닫기
            document.addEventListener('click', (e) => {
                if (!notificationBtn.contains(e.target) && !notificationMenu.contains(e.target)) {
                    notificationMenu.classList.remove('active');
                }
            });
        }

        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => {
                this.clearAllNotifications();
            });
        }
    },

    async loadNotifications() {
        try {
            const response = await fetch('/api/notification/list');
            const data = await response.json();
            
            if (data.success) {
                this.notifications = data.notifications;
                this.updateDropdownNotifications();
            }
        } catch (error) {
            console.error('알림 로드 중 오류:', error);
        }
    },

    async checkNewNotifications() {
        try {
            const lastId = this.notifications.length > 0 ? 
                Math.max(...this.notifications.map(n => n.id)) : 0;
            
            const response = await fetch(`/api/notification/new?last_id=${lastId}`);
            const data = await response.json();
            
            if (data.success && data.notifications.length > 0) {
                // 새로운 알림만 토스트로 표시
                data.notifications.forEach(notification => {
                    this.showToastNotification(notification);
                });
                
                // 기존 알림과 새 알림을 ID 기준으로 중복 제거하여 병합
                this.notifications = this.mergeNotifications(this.notifications, data.notifications);
                this.updateDropdownNotifications();
            }
        } catch (error) {
            console.error('새 알림 확인 중 오류:', error);
        }
    },

    // 알림 목록 병합 및 중복 제거 함수 추가
    mergeNotifications(existingNotifications, newNotifications) {
        const merged = [...existingNotifications];
        
        newNotifications.forEach(newNotif => {
            const existingIndex = merged.findIndex(existing => existing.id === newNotif.id);
            if (existingIndex === -1) {
                merged.push(newNotif);
            } else {
                // 기존 알림 업데이트
                merged[existingIndex] = newNotif;
            }
        });

        // timestamp 기준으로 정렬
        return merged.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    },

    showToastNotification(notification) {
        // 이미 표시된 알림이면 무시
        if (this.container.querySelector(`[data-id="${notification.id}"]`)) {
            return;
        }

        const notificationElement = document.createElement('div');
        notificationElement.className = `notification ${notification.type}`;
        notificationElement.dataset.id = notification.id;
        notificationElement.innerHTML = `
            <div class="notification-content">
                <h4>${notification.title}</h4>
                <p>${notification.message}</p>
            </div>
            <button class="close-btn" onclick="window.Notification.removeNotification(${notification.id}, true)">&times;</button>
        `;
        
        // 기존 타이머가 있다면 제거
        if (this.timers.has(notification.id)) {
            clearTimeout(this.timers.get(notification.id));
            this.timers.delete(notification.id);
        }
        
        // 새 타이머 설정 - 자동 숨김만 처리
        const timer = setTimeout(() => {
            this.hideNotification(notification.id);
            this.timers.delete(notification.id);
        }, 1000);
        
        this.timers.set(notification.id, timer);
        
        // 컨테이너에 알림 추가
        this.container.appendChild(notificationElement);
        
        // 최대 5개까지만 표시
        const notifications = this.container.querySelectorAll('.notification');
        if (notifications.length > 5) {
            notifications[0].remove();
        }
    },

    // 알림 숨김 처리 (읽음 처리 없이)
    async hideNotification(id) {
        const notificationElement = this.container.querySelector(`[data-id="${id}"]`);
        if (notificationElement) {
            notificationElement.classList.add('removing');
            await new Promise(resolve => setTimeout(resolve, 300));
            notificationElement.remove();
        }
    },

    // 알림 제거 (읽음 처리 포함)
    async removeNotification(id, markAsRead = false) {
        try {
            // 타이머가 있다면 제거
            if (this.timers.has(id)) {
                clearTimeout(this.timers.get(id));
                this.timers.delete(id);
            }

            // UI에서 알림 제거
            await this.hideNotification(id);

            // 읽음 처리가 필요한 경우에만 실행
            if (markAsRead) {
                const response = await fetch(`/api/notification/${id}/read`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const notification = this.notifications.find(n => n.id === id);
                    if (notification) {
                        notification.is_read = true;
                    }
                    this.updateDropdownNotifications();
                }
            }
        } catch (error) {
            console.error('알림 처리 중 오류:', error);
        }
    },

    async addNotification(type, title, message) {
        try {
            const response = await fetch('/api/notification/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ type, title, message })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const notification = data.notification;
                this.notifications.unshift(notification);
                this.showToastNotification(notification);
                this.updateDropdownNotifications();
                return data;
            }
        } catch (error) {
            console.error('알림 추가 중 오류:', error);
        }
    },

    async clearAllNotifications() {
        try {
            const response = await fetch('/api/notification/clear', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 모든 알림을 읽음 처리
                this.notifications.forEach(notification => {
                    notification.is_read = true;
                });
                this.renderNotifications();
                this.updateDropdownNotifications();
            }
        } catch (error) {
            console.error('알림 전체 읽음 처리 중 오류:', error);
        }
    },

    renderNotifications() {
        if (!this.container) return;

        const unreadNotifications = this.notifications
            .filter(n => !n.is_read)
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .slice(0, 5);  // 최근 5개의 읽지 않은 알림만 표시

        this.container.innerHTML = unreadNotifications
            .map(notification => `
                <div class="notification ${notification.type}" data-id="${notification.id}">
                    <div class="notification-content">
                        <h4>${notification.title}</h4>
                        <p>${notification.message}</p>
                    </div>
                    <button class="close-btn" onclick="window.Notification.removeNotification(${notification.id})">&times;</button>
                </div>
            `)
            .join('');
    },

    updateDropdownNotifications() {
        const notificationList = document.querySelector('.notification-list');
        const notificationEmpty = document.querySelector('.notification-empty');
        const notificationBadge = document.querySelector('.notification-badge');
        
        if (!notificationList || !notificationEmpty || !notificationBadge) return;

        const unreadCount = this.notifications.filter(n => !n.is_read).length;
        
        if (unreadCount > 0) {
            notificationBadge.textContent = unreadCount;
            notificationBadge.style.display = 'block';
        } else {
            notificationBadge.style.display = 'none';
        }

        if (this.notifications.length === 0) {
            notificationEmpty.style.display = 'block';
            notificationList.innerHTML = '';
            return;
        }

        notificationEmpty.style.display = 'none';
        notificationList.innerHTML = this.notifications
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
            .map(notification => `
                <div class="notification-item ${notification.is_read ? '' : 'unread'}">
                    <div class="title">${notification.title}</div>
                    <div class="message">${notification.message}</div>
                    <div class="time">${new Date(notification.timestamp).toLocaleString()}</div>
                </div>
            `)
            .join('');
    },

    // 페이지 새로고침 전 호출할 함수 추가
    beforeReload() {
        window.isReloading = true;
    }
}; 