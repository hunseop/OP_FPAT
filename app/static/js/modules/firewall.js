import { UI } from './ui.js';
import { Notification } from './notification.js';

export const Firewall = {
    initializeSync() {
        document.querySelectorAll('.sync-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = this.dataset.id;
                const originalText = this.textContent;
                const statusCell = this.closest('tr').querySelector('.sync-status');
                const firewallName = this.closest('tr').cells[0].textContent;
                
                if (this.disabled) {
                    Notification.addNotification('info', '동기화 진행 중', `${firewallName} 방화벽이 이미 동기화 중입니다.`);
                    return;
                }
                
                this.disabled = true;
                this.classList.add('syncing');
                
                statusCell.innerHTML = '<span class="sync-progress">동기화 중... <span class="progress-value">0</span>%</span>';
                statusCell.className = 'sync-status syncing';
                
                Notification.addNotification('info', '동기화 시작', `${firewallName} 방화벽 동기화를 시작합니다.`);
                
                this.startSync(id, firewallName, statusCell, this, originalText);
            });
        });
    },

    async startSync(id, firewallName, statusCell, button, originalText) {
        try {
            const response = await fetch(`/api/firewall/sync/${id}`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                this.checkProgress(id, firewallName, statusCell, button, originalText);
            } else {
                this.handleSyncError(firewallName, statusCell, button, originalText, data.error);
            }
        } catch (error) {
            this.handleSyncError(firewallName, statusCell, button, originalText, '동기화 요청 중 오류가 발생했습니다.');
        }
    },

    async checkProgress(id, firewallName, statusCell, button, originalText) {
        try {
            const response = await fetch(`/api/firewall/sync/status/${id}`);
            const progressData = await response.json();

            switch (progressData.state) {
                case 'SUCCESS':
                    this.handleSyncSuccess(firewallName, statusCell, button, originalText);
                    break;
                case 'PROGRESS':
                    statusCell.innerHTML = `<span class="sync-progress">동기화 중... <span class="progress-value">${progressData.progress}</span>%</span>`;
                    setTimeout(() => this.checkProgress(id, firewallName, statusCell, button, originalText), 1000);
                    break;
                case 'FAILURE':
                    this.handleSyncError(firewallName, statusCell, button, originalText, progressData.error);
                    break;
                case 'PENDING':
                    statusCell.innerHTML = '<span class="sync-progress">대기 중...</span>';
                    setTimeout(() => this.checkProgress(id, firewallName, statusCell, button, originalText), 1000);
                    break;
            }
        } catch (error) {
            this.handleSyncError(firewallName, statusCell, button, originalText, '상태 확인 중 오류가 발생했습니다.');
        }
    },

    handleSyncSuccess(firewallName, statusCell, button, originalText) {
        Notification.addNotification('success', '동기화 완료', `${firewallName} 방화벽 동기화가 완료되었습니다.`);
        const now = new Date().toLocaleString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
        statusCell.innerHTML = now;
        statusCell.className = 'sync-status';
        button.disabled = false;
        button.classList.remove('syncing');
        button.textContent = originalText;
        setTimeout(() => location.reload(), 1000);
    },

    handleSyncError(firewallName, statusCell, button, originalText, error) {
        Notification.addNotification('error', '동기화 실패', `${firewallName} 방화벽 동기화 중 오류가 발생했습니다: ${error}`);
        statusCell.innerHTML = '실패';
        statusCell.className = 'sync-status failed';
        button.disabled = false;
        button.classList.remove('syncing');
        button.textContent = originalText;
    }
}; 