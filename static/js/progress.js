class ProgressManager {
    constructor() {
        this.steps = document.querySelectorAll('.progress-step');
        this.initializeSteps();
        this.setupEventListeners();
    }

    initializeSteps() {
        this.steps.forEach(step => {
            step.classList.remove('active', 'complete');
        });

        const executeStep = this.steps[this.steps.length - 1];
        executeStep.style.display = 'flex';

        gsap.to('.progress-step', {
            opacity: 1,
            y: 0,
            duration: 0.8,
            stagger: 0.2,
            ease: 'power2.out'
        });

        gsap.to('.form-group', {
            opacity: 1,
            y: 0,
            duration: 0.8,
            stagger: 0.1,
            ease: 'power2.out'
        });
    }

    updateProgress() {
        const formData = this.getFormData();
        
        this.steps.forEach(step => {
            step.classList.remove('active', 'complete');
        });

        if (this.isAuthenticationComplete(formData)) {
            this.steps[0].classList.add('active');
            
            if (formData.firewallType) {
                this.steps[1].classList.add('active');
                
                if (formData.command && formData.subcommand) {
                    this.steps[2].classList.add('active');
                    this.steps[3].classList.add('complete');
                }
            }
        }

        const executeStep = this.steps[this.steps.length - 1];
        if (this.isAllFieldsFilled(formData)) {
            executeStep.classList.add('complete');
            executeStep.style.cursor = 'pointer';
        } else {
            executeStep.classList.remove('complete');
            executeStep.style.cursor = 'default';
        }
    }

    getFormData() {
        return {
            hostname: document.getElementById('hostname').value.trim(),
            username: document.getElementById('username').value.trim(),
            password: document.getElementById('password').value.trim(),
            firewallType: document.getElementById('firewallType').value,
            command: document.getElementById('command').value,
            subcommand: document.getElementById('subcommand').value
        };
    }

    isAuthenticationComplete(formData) {
        return formData.hostname && formData.username && formData.password;
    }

    isAllFieldsFilled(formData) {
        const basicFieldsFilled = this.isAuthenticationComplete(formData) && 
                                formData.firewallType && 
                                formData.command && 
                                formData.subcommand;
        
        if (!basicFieldsFilled) return false;

        const firewallType = formData.firewallType;
        const command = formData.command;
        const subcommand = formData.subcommand;
        const options = window.commands[firewallType][command][subcommand]?.options;

        if (options) {
            const optionsFields = document.getElementById('optionsFields')
                .querySelectorAll('input, select');
            
            const allOptionsFilled = Array.from(optionsFields).every(field => {
                const value = field.value.trim();
                return value !== '' && value !== 'Select ' + field.name.replace('option_', '');
            });

            return allOptionsFilled;
        }

        return true;
    }

    setupEventListeners() {
        ['hostname', 'username', 'password', 'firewallType', 'command', 'subcommand'].forEach(id => {
            const element = document.getElementById(id);
            ['change', 'input', 'keyup', 'paste'].forEach(event => {
                element.addEventListener(event, () => this.updateProgress());
            });
        });

        const optionsContainer = document.getElementById('optionsContainer');
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' || mutation.type === 'attributes') {
                    const optionsFields = document.getElementById('optionsFields')
                        .querySelectorAll('input, select');
                    
                    optionsFields.forEach(field => {
                        ['change', 'input', 'keyup', 'paste'].forEach(event => {
                            field.addEventListener(event, () => this.updateProgress());
                        });
                    });
                }
            });
        });

        observer.observe(optionsContainer, {
            childList: true,
            subtree: true,
            attributes: true
        });

        const executeStep = this.steps[this.steps.length - 1];
        executeStep.addEventListener('click', () => {
            if (executeStep.classList.contains('complete')) {
                document.getElementById('confirmModal').style.display = 'block';
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.progressManager = new ProgressManager();
}); 