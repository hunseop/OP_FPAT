class FormManager {
    constructor() {
        this.form = document.getElementById('commandForm');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // 비밀번호 토글 버튼
        document.getElementById('togglePassword').addEventListener('click', () => {
            const passwordInput = document.getElementById('password');
            const icon = document.querySelector('#togglePassword i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });

        // 방화벽 타입 변경
        document.getElementById('firewallType').addEventListener('change', (e) => {
            const commandSelect = document.getElementById('command');
            const selectedFw = e.target.value;
            
            commandSelect.innerHTML = '<option value="">Select Command</option>';
            if (selectedFw) {
                Object.keys(window.commands[selectedFw]).forEach(cmd => {
                    commandSelect.add(new Option(cmd, cmd));
                });
                commandSelect.disabled = false;
            } else {
                commandSelect.disabled = true;
            }
            document.getElementById('subcommand').disabled = true;
            document.getElementById('optionsContainer').style.display = 'none';
        });

        // 명령어 변경
        document.getElementById('command').addEventListener('change', (e) => {
            const subcommandSelect = document.getElementById('subcommand');
            const firewallType = document.getElementById('firewallType').value;
            const selectedCmd = e.target.value;
            
            subcommandSelect.innerHTML = '<option value="">Select Subcommand</option>';
            if (selectedCmd) {
                Object.keys(window.commands[firewallType][selectedCmd]).forEach(subcmd => {
                    subcommandSelect.add(new Option(subcmd, subcmd));
                });
                subcommandSelect.disabled = false;
            } else {
                subcommandSelect.disabled = true;
            }
            document.getElementById('optionsContainer').style.display = 'none';
        });

        // 서브커맨드 변경
        document.getElementById('subcommand').addEventListener('change', (e) => {
            const firewallType = document.getElementById('firewallType').value;
            const command = document.getElementById('command').value;
            const subcommand = e.target.value;
            
            this.updateOptionsFields(firewallType, command, subcommand);
        });

        // 폼 제출 방지
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
        });
    }

    updateOptionsFields(firewallType, command, subcommand) {
        const optionsContainer = document.getElementById('optionsContainer');
        const optionsFields = document.getElementById('optionsFields');
        const options = window.commands[firewallType][command][subcommand]?.options;
        
        optionsFields.innerHTML = '';
        
        if (options) {
            optionsContainer.style.display = 'block';
            gsap.fromTo(optionsContainer, 
                { opacity: 0, y: 20 },
                { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out' }
            );

            Object.entries(options).forEach(([key, value]) => {
                const div = document.createElement('div');
                div.className = 'col-md-6 mb-3';
                
                if (Array.isArray(value)) {
                    div.innerHTML = `
                        <select class="form-control" id="option_${key}" name="option_${key}">
                            <option value="">Select ${key}</option>
                            ${value.map(v => `<option value="${v}">${v}</option>`).join('')}
                        </select>
                    `;
                } else {
                    div.innerHTML = `
                        <input type="text" class="form-control" id="option_${key}" name="option_${key}" 
                               value="${value}" placeholder="${key}">
                    `;
                }
                
                optionsFields.appendChild(div);
                gsap.from(div, {
                    opacity: 0,
                    y: 20,
                    duration: 0.5,
                    delay: 0.1,
                    ease: 'power2.out'
                });
            });
        } else {
            optionsContainer.style.display = 'none';
        }
    }

    getFormData() {
        const options = {};
        const optionsFields = document.getElementById('optionsFields').querySelectorAll('input, select');
        optionsFields.forEach(field => {
            options[field.name.replace('option_', '')] = field.value;
        });

        return {
            hostname: document.getElementById('hostname').value,
            username: document.getElementById('username').value,
            password: document.getElementById('password').value,
            firewall_type: document.getElementById('firewallType').value,
            command: document.getElementById('command').value,
            subcommand: document.getElementById('subcommand').value,
            options: options
        };
    }
}

// DOM이 로드되면 FormManager 인스턴스 생성
document.addEventListener('DOMContentLoaded', () => {
    window.formManager = new FormManager();
}); 