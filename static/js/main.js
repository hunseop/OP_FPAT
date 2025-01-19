// 전역 상태 관리
const state = {
    commands: window.state.commands,
    predefinedHosts: window.state.predefinedHosts,
    currentEditingHost: null,
    currentDeletingHost: null,
    currentFocus: -1,
    suggestions: []
};

// DOM 요소
const elements = {
    hostnameInput: document.getElementById('hostname'),
    usernameInput: document.getElementById('username'),
    passwordInput: document.getElementById('password'),
    firewallTypeSelect: document.getElementById('firewallType'),
    commandSelect: document.getElementById('command'),
    subcommandSelect: document.getElementById('subcommand'),
    optionsContainer: document.getElementById('optionsContainer'),
    optionsFields: document.getElementById('optionsFields'),
    commandForm: document.getElementById('commandForm'),
    result: document.getElementById('result'),
    hostSuggestions: document.createElement('div')
};

// 초기화
function init() {
    setupHostnameSuggestions();
    setupEventListeners();
    setupFormHandlers();
}

// 이벤트 리스너 설정
function setupEventListeners() {
    elements.firewallTypeSelect.addEventListener('change', handleFirewallTypeChange);
    elements.commandSelect.addEventListener('change', handleCommandChange);
    elements.subcommandSelect.addEventListener('change', handleSubcommandChange);
    elements.commandForm.addEventListener('submit', handleFormSubmit);
    
    // 호스트네임 자동완성 관련 이벤트
    elements.hostnameInput.addEventListener('keydown', handleHostnameKeydown);
    elements.hostnameInput.addEventListener('input', handleHostnameInput);
    elements.hostnameInput.addEventListener('focus', handleHostnameFocus);
    
    // 문서 전체 클릭 이벤트
    document.addEventListener('click', handleDocumentClick);
}

// 폼 핸들러 설정
function setupFormHandlers() {
    // 옵션 필드 변경 이벤트 처리
    elements.optionsFields.addEventListener('change', (e) => {
        const target = e.target;
        if (target.matches('select, input')) {
            validateOptionField(target);
        }
    });

    // 옵션 필드 입력 이벤트 처리
    elements.optionsFields.addEventListener('input', (e) => {
        const target = e.target;
        if (target.matches('input[type="text"], input[type="number"]')) {
            validateOptionField(target);
        }
    });
}

// 호스트네임 자동완성 설정
function setupHostnameSuggestions() {
    elements.hostSuggestions.className = 'suggestions-container';
    elements.hostnameInput.parentNode.appendChild(elements.hostSuggestions);
}

// 호스트네임 키 입력 핸들러
function handleHostnameKeydown(e) {
    const suggestions = elements.hostSuggestions.getElementsByClassName('suggestion-item');
    if (suggestions.length === 0) return;

    switch (e.key) {
        case 'ArrowUp':
            e.preventDefault();
            state.currentFocus--;
            if (state.currentFocus < 0) state.currentFocus = suggestions.length - 1;
            setActiveSuggestion(suggestions);
            break;

        case 'ArrowDown':
            e.preventDefault();
            state.currentFocus++;
            if (state.currentFocus >= suggestions.length) state.currentFocus = 0;
            setActiveSuggestion(suggestions);
            break;

        case 'Enter':
            e.preventDefault();
            if (state.currentFocus > -1 && suggestions[state.currentFocus]) {
                const selectedItem = suggestions[state.currentFocus];
                const hostname = selectedItem.dataset.hostname;
                const host = state.predefinedHosts[hostname];
                
                elements.hostnameInput.value = hostname;
                elements.usernameInput.value = host.username || '';
                elements.passwordInput.value = host.password || '';
                
                hideSuggestions();
            }
            break;

        case 'Escape':
            hideSuggestions();
            break;
    }
}

// 호스트네임 입력 핸들러
function handleHostnameInput(e) {
    const value = e.target.value.toLowerCase();
    
    // 입력값이 변경될 때마다 기존 값과 연결 해제
    const currentHost = state.predefinedHosts[value];
    if (!currentHost) {
        elements.usernameInput.value = '';
        elements.passwordInput.value = '';
    }
    
    const matches = Object.entries(state.predefinedHosts).filter(([hostname, info]) => 
        hostname.toLowerCase().includes(value) || 
        info.alias.toLowerCase().includes(value)
    );

    if (matches.length > 0 && value) {
        showSuggestions(matches);
    } else {
        hideSuggestions();
    }
}

// 호스트네임 포커스 핸들러
function handleHostnameFocus() {
    const value = elements.hostnameInput.value.toLowerCase();
    const matches = Object.entries(state.predefinedHosts).filter(([hostname, info]) => 
        hostname.toLowerCase().includes(value) || 
        info.alias.toLowerCase().includes(value)
    );

    if (matches.length > 0) {
        showSuggestions(matches);
    }
}

// 문서 클릭 핸들러
function handleDocumentClick(e) {
    if (!elements.hostnameInput.contains(e.target) && 
        !elements.hostSuggestions.contains(e.target)) {
        hideSuggestions();
    }
}

// 자동완성 제안 표시
function showSuggestions(matches) {
    elements.hostSuggestions.innerHTML = matches.map(([hostname, info]) => `
        <div class="suggestion-item" data-hostname="${hostname}">
            <div class="suggestion-host">${hostname}</div>
            <div class="suggestion-alias">${info.alias}</div>
        </div>
    `).join('');

    elements.hostSuggestions.style.display = 'block';

    // 제안 클릭 이벤트 설정
    elements.hostSuggestions.querySelectorAll('.suggestion-item').forEach(item => {
        item.addEventListener('click', () => {
            const hostname = item.dataset.hostname;
            const host = state.predefinedHosts[hostname];
            
            // 호스트네임 선택 시 항상 모든 필드 업데이트
            elements.hostnameInput.value = hostname;
            elements.usernameInput.value = host.username || '';
            elements.passwordInput.value = host.password || '';
            
            hideSuggestions();
        });
    });
}

// 자동완성 제안 숨기기
function hideSuggestions() {
    elements.hostSuggestions.style.display = 'none';
    state.currentFocus = -1;
}

// 활성 제안 설정
function setActiveSuggestion(suggestions) {
    Array.from(suggestions).forEach((item, index) => {
        if (index === state.currentFocus) {
            item.classList.add('active');
            item.scrollIntoView({ block: 'nearest' });
        } else {
            item.classList.remove('active');
        }
    });
}

// 옵션 필드 검증
function validateOptionField(field) {
    const value = field.value;
    const name = field.name.replace('option_', '');
    const firewallType = elements.firewallTypeSelect.value;
    const command = elements.commandSelect.value;
    const subcommand = elements.subcommandSelect.value;
    
    // 옵션 데이터 접근 방식 수정
    const option = state.commands[firewallType][command][subcommand][name];
    
    if (!option) return true;
    
    if (option.required && !value) {
        field.classList.add('error');
        return false;
    }
    
    if (option.type === 'number') {
        const num = Number(value);
        if (isNaN(num) || 
            (option.min !== undefined && num < option.min) || 
            (option.max !== undefined && num > option.max)) {
            field.classList.add('error');
            return false;
        }
    }
    
    if (option.pattern && !new RegExp(option.pattern).test(value)) {
        field.classList.add('error');
        return false;
    }
    
    field.classList.remove('error');
    return true;
}

// 방화벽 타입 변경 핸들러
function handleFirewallTypeChange(e) {
    const firewallType = e.target.value;
    const commands = state.commands[firewallType] || {};
    
    // 커맨드 선택 업데이트
    elements.commandSelect.innerHTML = `
        <option value="">Select Command</option>
        ${Object.keys(commands).map(cmd => `
            <option value="${cmd}">${cmd}</option>
        `).join('')}
    `;
    
    // 커맨드 선택 활성화/비활성화
    elements.commandSelect.disabled = !firewallType;
    
    // 서브커맨드 초기화
    elements.subcommandSelect.innerHTML = '<option value="">Select command first</option>';
    elements.subcommandSelect.disabled = true;
    
    // 옵션 필드 초기화
    elements.optionsContainer.classList.remove('visible');
    elements.optionsFields.innerHTML = '';
}

// 커맨드 변경 핸들러
function handleCommandChange(e) {
    const firewallType = elements.firewallTypeSelect.value;
    const command = e.target.value;
    const commandData = state.commands[firewallType]?.[command];
    
    // 서브커맨드 선택 업데이트
    elements.subcommandSelect.innerHTML = `
        <option value="">Select Subcommand</option>
        ${Object.keys(commandData || {}).filter(key => key !== 'options').map(subcmd => `
            <option value="${subcmd}">${subcmd}</option>
        `).join('')}
    `;
    
    // 서브커맨드 선택 활성화/비활성화
    elements.subcommandSelect.disabled = !command;
    
    // 옵션 필드 초기화
    elements.optionsContainer.classList.remove('visible');
    elements.optionsFields.innerHTML = '';
}

// 서브커맨드 변경 핸들러
function handleSubcommandChange(e) {
    const firewallType = elements.firewallTypeSelect.value;
    const command = elements.commandSelect.value;
    const subcommand = e.target.value;
    
    console.log('State commands:', state.commands);
    console.log('Selected values:', { firewallType, command, subcommand });
    
    if (!firewallType || !command || !subcommand) {
        elements.optionsContainer.classList.remove('visible');
        elements.optionsFields.innerHTML = '';
        return;
    }
    
    // 안전한 객체 접근을 위한 체크
    const firewallCommands = state.commands?.[firewallType];
    if (!firewallCommands) {
        console.error(`No commands found for firewall type: ${firewallType}`);
        return;
    }
    
    const commandObj = firewallCommands?.[command];
    if (!commandObj) {
        console.error(`No command object found for command: ${command}`);
        return;
    }
    
    const subcommandObj = commandObj?.[subcommand];
    if (!subcommandObj) {
        console.error(`No subcommand object found for subcommand: ${subcommand}`);
        return;
    }
    
    // 옵션 데이터 접근
    const options = subcommandObj.options || {};
    console.log('Options:', options);
    
    if (Object.keys(options).length === 0) {
        elements.optionsContainer.classList.remove('visible');
        elements.optionsFields.innerHTML = '';
        return;
    }
    
    // 옵션 필드 생성
    elements.optionsFields.innerHTML = Object.entries(options).map(([key, option]) => `
        <div class="form-group">
            <label class="form-label" for="option_${key}">${key}</label>
            ${createOptionInput(key, option)}
        </div>
    `).join('');
    
    elements.optionsContainer.classList.add('visible');
}

// 옵션 입력 필드 생성
function createOptionInput(key, option) {
    // 옵션이 배열인 경우 select 타입으로 처리
    if (Array.isArray(option)) {
        const defaultValue = option[0] || '';
        return `
            <select class="form-control" name="option_${key}" id="option_${key}">
                ${option.map(value => `
                    <option value="${value}" ${value === defaultValue ? 'selected' : ''}>${value}</option>
                `).join('')}
            </select>
        `;
    }
    
    // 옵션이 객체이고 type 속성이 있는 경우
    if (typeof option === 'object' && option !== null) {
        if (Array.isArray(option.type)) {
            const defaultValue = option.type[0] || '';
            return `
                <select class="form-control" name="option_${key}" id="option_${key}">
                    ${option.type.map(value => `
                        <option value="${value}" ${value === defaultValue ? 'selected' : ''}>${value}</option>
                    `).join('')}
                </select>
            `;
        }
        
        // 기본값이 있는 경우
        const defaultValue = option.default || '';
        return `
            <input type="text" 
                   class="form-control" 
                   name="option_${key}" 
                   id="option_${key}"
                   value="${defaultValue}"
                   placeholder="${key}">
        `;
    }
    
    // 기본 text input
    return `
        <input type="text" 
               class="form-control" 
               name="option_${key}" 
               id="option_${key}"
               placeholder="${key}">
    `;
}

// 폼 제출 핸들러
async function handleFormSubmit(e) {
    e.preventDefault();
    
    try {
        const formData = getFormData();
        
        // 옵션 필드 검증
        const optionsFields = elements.optionsFields.querySelectorAll('input, select');
        let hasError = false;
        
        optionsFields.forEach(field => {
            if (!validateOptionField(field)) {
                hasError = true;
            }
        });
        
        if (hasError) {
            throw new Error('Please fill in all required options correctly.');
        }
        
        await submitForm(formData);
    } catch (error) {
        showError(error);
    }
}

// 폼 데이터 수집
function getFormData() {
    const options = {};
    const optionsFields = elements.optionsFields.querySelectorAll('input, select');
    
    optionsFields.forEach(field => {
        const value = field.value.trim();
        // 값이 있는 경우에만 options에 추가
        if (value) {
            options[field.name.replace('option_', '')] = value;
        }
    });

    return {
        hostname: elements.hostnameInput.value,
        username: elements.usernameInput.value,
        password: elements.passwordInput.value,
        firewall_type: elements.firewallTypeSelect.value,
        command: elements.commandSelect.value,
        subcommand: elements.subcommandSelect.value,
        options: options
    };
}

// 폼 제출
async function submitForm(data) {
    const submitButton = elements.commandForm.querySelector('button[type="submit"]');
    const inputs = document.querySelectorAll('input, select');
    
    try {
        disableFormElements(inputs, submitButton);
        showLoadingState();
        
        const response = await fetch('/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to execute command. Please try again.');
        }
        
        const result = await response.json();
        showResult(result);
    } catch (error) {
        showError(error);
    } finally {
        enableFormElements(inputs, submitButton);
    }
}

// 유틸리티 함수들
function disableFormElements(inputs, submitButton) {
    inputs.forEach(input => input.disabled = true);
    submitButton.disabled = true;
}

function enableFormElements(inputs, submitButton) {
    inputs.forEach(input => {
        input.disabled = false;
        if (input.id === 'command') {
            input.disabled = !elements.firewallTypeSelect.value;
        } else if (input.id === 'subcommand') {
            input.disabled = !elements.commandSelect.value;
        }
    });
    submitButton.disabled = false;
}

function showLoadingState() {
    elements.result.innerHTML = `
        <div class="result loading">
            <div class="loading-message">Executing command, please wait...</div>
            <div class="loading-animation"></div>
        </div>
    `;
}

function showResult(result) {
    elements.result.innerHTML = `
        <div class="result ${result.status === 'success' ? 'success' : 'error'}">
            ${result.message}
        </div>
    `;
}

function showError(error) {
    elements.result.innerHTML = `
        <div class="result error">
            ${error.message}
        </div>
    `;
}

// 초기화 실행
document.addEventListener('DOMContentLoaded', init);