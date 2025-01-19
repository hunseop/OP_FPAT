// 호스트 관리 모달 요소
const modalElements = {
    modal: document.getElementById('hostsModal'),
    addModal: document.getElementById('addHostModal'),
    editModal: document.getElementById('editHostModal'),
    deleteModal: document.getElementById('deleteHostModal'),
    settingsIcon: document.getElementById('hostsSettings'),
    closeBtn: document.querySelector('#hostsModal .close'),
    addHostButton: document.getElementById('addHostButton'),
    hostsTableBody: document.getElementById('hostsTableBody'),
    searchInput: document.getElementById('hostSearch'),
    emptyState: document.getElementById('emptyState')
};

// 초기화
function initHostManagement() {
    setupModalEventListeners();
    setupSearchFunctionality();
}

// 모달 이벤트 리스너 설정
function setupModalEventListeners() {
    modalElements.settingsIcon.addEventListener('click', () => {
        modalElements.modal.style.display = 'block';
        refreshHostsTable();
    });

    modalElements.closeBtn.addEventListener('click', () => {
        modalElements.modal.style.display = 'none';
    });

    modalElements.addHostButton.addEventListener('click', addHost);

    // ESC 키 처리
    document.addEventListener('keydown', handleEscapeKey);
    
    // 모달 Enter 키 처리
    modalElements.addModal.addEventListener('keydown', handleModalEnterKey);
    modalElements.editModal.addEventListener('keydown', handleModalEnterKey);
}

// 호스트 테이블 새로고침
async function refreshHostsTable() {
    try {
        const response = await fetch('/api/hosts');
        const hosts = await response.json();
        state.predefinedHosts = hosts;
        
        updateHostsTable(hosts);
    } catch (error) {
        showNotification('Failed to refresh hosts table', 'error');
    }
}

// 호스트 테이블 업데이트
function updateHostsTable(hosts) {
    modalElements.hostsTableBody.innerHTML = '';
    const entries = Object.entries(hosts);
    
    if (entries.length === 0) {
        showEmptyState(true);
    } else {
        showEmptyState(false);
        renderHostsTable(entries);
    }
}

// 호스트 테이블 렌더링
function renderHostsTable(entries) {
    entries.forEach(([hostname, info]) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${hostname}</td>
            <td>${info.alias}</td>
            <td>${info.username}</td>
            <td class="action-buttons">
                <button class="action-button edit-button" onclick="editHost('${hostname}')">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="action-button delete-button" onclick="deleteHostClick('${hostname}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        `;
        modalElements.hostsTableBody.appendChild(row);
    });
}

// 빈 상태 표시/숨김
function showEmptyState(show) {
    modalElements.emptyState.style.display = show ? 'block' : 'none';
    document.querySelector('.hosts-table').style.display = show ? 'none' : 'table';
}

// 호스트 추가
function addHost() {
    modalElements.addModal.style.display = 'block';
    clearAddModalInputs();
}

// 호스트 수정
async function editHost(hostname) {
    state.currentEditingHost = hostname;
    try {
        const hosts = await fetchHosts();
        const host = hosts[hostname];
        if (!host) {
            showNotification('Host not found', 'error');
            return;
        }

        populateEditModal(hostname, host);
        modalElements.editModal.style.display = 'block';
    } catch (error) {
        showNotification('Failed to load host data', 'error');
    }
}

// 호스트 삭제 클릭
function deleteHostClick(hostname) {
    state.currentDeletingHost = hostname;
    modalElements.deleteModal.style.display = 'block';
}

// 모달 닫기 함수들
function closeAddModal() {
    modalElements.addModal.style.display = 'none';
}

function closeEditModal() {
    modalElements.editModal.style.display = 'none';
    state.currentEditingHost = null;
}

function closeDeleteModal() {
    modalElements.deleteModal.style.display = 'none';
    state.currentDeletingHost = null;
}

// 호스트 저장 함수들
async function saveNewHost() {
    const hostData = getHostFormData('add');
    const errors = validateHostInput(hostData);
    
    if (errors.length > 0) {
        showNotification(errors.join('\n'), 'error');
        return;
    }

    try {
        const result = await saveHost(hostData, 'POST');
        if (!result.error) {
            await refreshHostsTable();
            closeAddModal();
            showNotification('Host added successfully');
        } else {
            showNotification(result.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to add host', 'error');
    }
}

async function saveHostEdit() {
    const hostData = getHostFormData('edit');
    const errors = validateHostInput(hostData);
    
    if (errors.length > 0) {
        showNotification(errors.join('\n'), 'error');
        return;
    }

    try {
        if (hostData.hostname !== state.currentEditingHost) {
            await deleteHost(state.currentEditingHost);
            await saveHost(hostData, 'POST');
        } else {
            await saveHost(hostData, 'PUT');
        }
        
        await refreshHostsTable();
        closeEditModal();
        showNotification('Host updated successfully');
    } catch (error) {
        showNotification('Failed to update host', 'error');
    }
}

async function confirmDeleteHost() {
    try {
        const result = await deleteHost(state.currentDeletingHost);
        if (!result.error) {
            await refreshHostsTable();
            closeDeleteModal();
            showNotification('Host deleted successfully');
        } else {
            showNotification(result.error, 'error');
        }
    } catch (error) {
        showNotification('Failed to delete host', 'error');
    }
}

// 유틸리티 함수들
function getHostFormData(type) {
    const prefix = type === 'add' ? 'add' : 'edit';
    return {
        hostname: document.getElementById(`${prefix}Hostname`).value,
        alias: document.getElementById(`${prefix}Alias`).value,
        username: document.getElementById(`${prefix}Username`).value,
        password: document.getElementById(`${prefix}Password`).value
    };
}

function validateHostInput(data) {
    const errors = [];
    
    if (!data.hostname) errors.push('Hostname is required');
    else if (!/^[a-zA-Z0-9.-]+$/.test(data.hostname)) {
        errors.push('Hostname can only contain letters, numbers, dots, and hyphens');
    }
    
    if (!data.alias) errors.push('Alias is required');
    if (!data.username) errors.push('Username is required');
    if (!data.password) errors.push('Password is required');
    
    return errors;
}

async function saveHost(data, method) {
    const response = await fetch('/api/hosts', {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return await response.json();
}

async function deleteHost(hostname) {
    const response = await fetch('/api/hosts', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hostname })
    });
    return await response.json();
}

async function fetchHosts() {
    const response = await fetch('/api/hosts');
    return await response.json();
}

function clearAddModalInputs() {
    document.getElementById('addHostname').value = '';
    document.getElementById('addAlias').value = '';
    document.getElementById('addUsername').value = '';
    document.getElementById('addPassword').value = '';
}

function populateEditModal(hostname, host) {
    document.getElementById('editHostname').value = hostname;
    document.getElementById('editAlias').value = host.alias;
    document.getElementById('editUsername').value = host.username;
    document.getElementById('editPassword').value = host.password;
}

// 키 이벤트 핸들러
function handleEscapeKey(e) {
    if (e.key === 'Escape') {
        if (modalElements.addModal.style.display === 'block') {
            closeAddModal();
        } else if (modalElements.editModal.style.display === 'block') {
            closeEditModal();
        } else if (modalElements.deleteModal.style.display === 'block') {
            closeDeleteModal();
        } else {
            modalElements.modal.style.display = 'none';
        }
    }
}

function handleModalEnterKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (e.target.closest('#addHostModal')) {
            saveNewHost();
        } else if (e.target.closest('#editHostModal')) {
            saveHostEdit();
        }
    }
}

// 검색 기능 설정
function setupSearchFunctionality() {
    modalElements.searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const rows = modalElements.hostsTableBody.getElementsByTagName('tr');
        
        Array.from(rows).forEach(row => {
            const hostname = row.cells[0].textContent.toLowerCase();
            const alias = row.cells[1].textContent.toLowerCase();
            const matches = hostname.includes(searchTerm) || alias.includes(searchTerm);
            row.style.display = matches ? '' : 'none';
        });
    });
}

// 알림 표시
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
        ${message}
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);

    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// 초기화 실행
document.addEventListener('DOMContentLoaded', initHostManagement); 