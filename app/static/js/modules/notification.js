export const Notification = {
    notifications: [],
    unreadCount: 0,

    initialize() {
        const notificationBtn = document.getElementById('notificationBtn');
        const notificationMenu = document.querySelector('.notification-menu');
        const clearAllBtn = document.querySelector('.clear-all');
        
        // 알림 버튼 클릭 이벤트
        if (notificationBtn) {
            notificationBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                notificationMenu.classList.toggle('active');
                this.updateNotificationList();
            });
        }

        // 모두 읽음 버튼 클릭 이벤트
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.clearAllNotifications();
            });
        }

        // 문서 클릭시 드롭다운 닫기
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.notification-dropdown')) {
                notificationMenu.classList.remove('active');
            }
        });
    },

    addNotification(type, title, message) {
        const notification = {
            id: Date.now(),
            type,
            title,
            message,
            time: new Date(),
            read: false
        };

        this.notifications.unshift(notification);
        this.updateUnreadCount();
        this.updateNotificationList();
        
        return notification;
    },

    updateUnreadCount() {
        this.unreadCount = this.notifications.filter(n => !n.read).length;
        const badge = document.querySelector('.notification-badge');
        
        if (this.unreadCount > 0) {
            badge.textContent = this.unreadCount;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    },

    updateNotificationList() {
        const list = document.querySelector('.notification-list');
        const empty = document.querySelector('.notification-empty');
        
        if (this.notifications.length === 0) {
            list.innerHTML = '';
            empty.style.display = 'block';
            return;
        }

        empty.style.display = 'none';
        list.innerHTML = this.notifications.map(notification => `
            <div class="notification-item ${notification.read ? '' : 'unread'}" data-id="${notification.id}">
                <div class="title">${notification.title}</div>
                <div class="message">${notification.message}</div>
                <div class="time">${this.formatTime(notification.time)}</div>
            </div>
        `).join('');

        // 알림 클릭 이벤트 추가
        list.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', () => {
                const id = parseInt(item.dataset.id);
                this.markAsRead(id);
            });
        });
    },

    markAsRead(id) {
        const notification = this.notifications.find(n => n.id === id);
        if (notification && !notification.read) {
            notification.read = true;
            this.updateUnreadCount();
            this.updateNotificationList();
        }
    },

    clearAllNotifications() {
        this.notifications.forEach(n => n.read = true);
        this.updateUnreadCount();
        this.updateNotificationList();
    },

    formatTime(date) {
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // 1분 이내
            return '방금 전';
        } else if (diff < 3600000) { // 1시간 이내
            return `${Math.floor(diff / 60000)}분 전`;
        } else if (diff < 86400000) { // 1일 이내
            return `${Math.floor(diff / 3600000)}시간 전`;
        } else {
            return date.toLocaleString('ko-KR', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            });
        }
    }
}; 