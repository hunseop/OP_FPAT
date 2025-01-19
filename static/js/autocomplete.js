class Autocomplete {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            onSelect: options.onSelect || (() => {}),
            getData: options.getData || (() => []),
            getSearchFields: options.getSearchFields || ((item) => [item]),
            formatSuggestion: options.formatSuggestion || ((item) => item),
            ...options
        };
        
        this.suggestions = document.createElement('div');
        this.suggestions.className = 'suggestions-container';
        this.currentFocus = -1;
        
        this.setupElements();
        this.setupEventListeners();
    }
    
    setupElements() {
        this.input.parentNode.appendChild(this.suggestions);
    }
    
    setupEventListeners() {
        this.input.addEventListener('input', () => this.onInput());
        this.input.addEventListener('focus', () => this.onFocus());
        this.input.addEventListener('keydown', (e) => this.onKeyDown(e));
        
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.suggestions.contains(e.target)) {
                this.hideSuggestions();
            }
        });
        
        this.suggestions.addEventListener('click', (e) => this.handleSuggestionClick(e));
    }
    
    async onInput() {
        const value = this.input.value;
        const items = await this.options.getData();
        const matches = this.filterItems(items, value);
        
        if (matches.length > 0 && value) {
            this.showSuggestions(matches);
        } else {
            this.hideSuggestions();
        }
    }
    
    async onFocus() {
        const value = this.input.value;
        const items = await this.options.getData();
        const matches = value ? this.filterItems(items, value) : items;
        
        if (matches.length > 0) {
            this.showSuggestions(matches);
        }
    }
    
    onKeyDown(e) {
        const items = this.suggestions.getElementsByClassName('suggestion-item');
        if (items.length === 0) return;
        
        switch (e.key) {
            case 'ArrowUp':
                e.preventDefault();
                this.currentFocus--;
                if (this.currentFocus < 0) this.currentFocus = items.length - 1;
                this.setActiveSuggestion(items);
                break;
                
            case 'ArrowDown':
                e.preventDefault();
                this.currentFocus++;
                if (this.currentFocus >= items.length) this.currentFocus = 0;
                this.setActiveSuggestion(items);
                break;
                
            case 'Enter':
                e.preventDefault();
                let selectedItem = this.currentFocus > -1 
                    ? items[this.currentFocus] 
                    : items[0];
                    
                if (selectedItem) {
                    this.selectSuggestion(selectedItem);
                }
                break;
        }
    }
    
    filterItems(items, query) {
        return items.filter(item => {
            const searchFields = this.options.getSearchFields(item);
            return searchFields.some(field => 
                this.normalizeString(field).includes(this.normalizeString(query))
            );
        });
    }
    
    showSuggestions(items) {
        this.suggestions.innerHTML = items
            .map(item => this.options.formatSuggestion(item))
            .join('');
        this.suggestions.style.display = 'block';
    }
    
    hideSuggestions() {
        this.suggestions.style.display = 'none';
        this.currentFocus = -1;
    }
    
    setActiveSuggestion(items) {
        Array.from(items).forEach(item => item.classList.remove('active'));
        if (this.currentFocus >= 0) {
            items[this.currentFocus].classList.add('active');
            items[this.currentFocus].scrollIntoView({ block: 'nearest' });
        }
    }
    
    handleSuggestionClick(e) {
        let selectedItem = e.target.closest('.suggestion-item');
        if (selectedItem) {
            this.selectSuggestion(selectedItem);
        }
    }
    
    selectSuggestion(element) {
        const value = element.dataset.value;
        this.input.value = value;
        this.options.onSelect(value);
        this.hideSuggestions();
    }
    
    normalizeString(str) {
        return str.normalize('NFC').toLowerCase().trim();
    }
}

// 호스트네임 자동완성 초기화
function initHostnameAutocomplete() {
    const hostnameInput = document.getElementById('hostname');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    new Autocomplete(hostnameInput, {
        getData: async () => {
            const response = await fetch('/api/hosts');
            const hosts = await response.json();
            return Object.entries(hosts).map(([hostname, info]) => ({
                hostname,
                ...info
            }));
        },
        getSearchFields: (item) => [item.hostname, item.alias],
        formatSuggestion: (item) => `
            <div class="suggestion-item" data-value="${item.hostname}">
                <div class="suggestion-host">${item.hostname}</div>
                <div class="suggestion-alias">${item.alias}</div>
            </div>
        `,
        onSelect: (hostname) => {
            const hosts = state.predefinedHosts;
            if (hosts[hostname]) {
                usernameInput.value = hosts[hostname].username;
                passwordInput.value = hosts[hostname].password;
            }
        }
    });
}

// 초기화 실행
document.addEventListener('DOMContentLoaded', initHostnameAutocomplete); 