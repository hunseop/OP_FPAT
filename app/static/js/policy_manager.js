/**
 * 정책 관리자 JavaScript
 * 정책 분석 워크플로우를 관리하는 스크립트
 */

document.addEventListener('DOMContentLoaded', function() {
    // 워크플로우 상태 관리
    const workflowState = {
        workflowId: null,
        currentStep: null,
        steps: {
            initialized: false,
            request_processed: false,
            usage_processed: false,
            vendor_processed: false,
            duplicates_analyzed: false,
            reports_generated: false
        },
        files: {
            intermediate: [],
            reports: []
        }
    };

    // DOM 요소
    const initForm = document.getElementById('initForm');
    const requestForm = document.getElementById('requestForm');
    const usageForm = document.getElementById('usageForm');
    const vendorProcessBtn = document.getElementById('vendorProcessBtn');
    const duplicateAnalysisBtn = document.getElementById('duplicateAnalysisBtn');
    const generateReportsBtn = document.getElementById('generateReportsBtn');
    const downloadAllBtn = document.getElementById('downloadAllBtn');
    const intermediateFilesList = document.getElementById('intermediateFiles');
    const reportFilesList = document.getElementById('reportFiles');
    const modal = document.getElementById('workflowModal');
    const closeModalBtn = modal.querySelector('.close-btn');
    const progressFill = modal.querySelector('.progress-fill');
    const progressText = modal.querySelector('.progress-text');
    const statusMessage = modal.querySelector('.status-message');
    const noResults = document.querySelector('.no-results');
    const resultsFiles = document.querySelector('.results-files');

    // 이벤트 리스너 등록
    if (initForm) initForm.addEventListener('submit', handleInitialize);
    if (requestForm) requestForm.addEventListener('submit', handleRequestProcess);
    if (usageForm) usageForm.addEventListener('submit', handleUsageProcess);
    if (vendorProcessBtn) vendorProcessBtn.addEventListener('click', handleVendorProcess);
    if (duplicateAnalysisBtn) duplicateAnalysisBtn.addEventListener('click', handleDuplicateAnalysis);
    if (generateReportsBtn) generateReportsBtn.addEventListener('click', handleReportGeneration);
    if (downloadAllBtn) downloadAllBtn.addEventListener('click', handleDownloadAll);
    if (closeModalBtn) closeModalBtn.addEventListener('click', closeModal);

    /**
     * 새 워크플로우 시작
     */
    function startNewWorkflow() {
        // API 호출하여 새 워크플로우 ID 생성
        fetch('/api/policy_manager/create_workflow', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                workflowState.workflowId = data.workflow_id;
                console.log('새 워크플로우 생성:', workflowState.workflowId);
            } else {
                showNotification('워크플로우 생성 실패: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('워크플로우 생성 오류:', error);
            showNotification('워크플로우 생성 중 오류가 발생했습니다.', 'error');
        });
    }

    /**
     * 초기화 단계 처리
     */
    function handleInitialize(event) {
        event.preventDefault();
        
        const formData = new FormData(initForm);
        
        // 필수 필드 검증
        const policyFile = formData.get('policy_file');
        const vendor = formData.get('vendor');
        
        if (!policyFile || !policyFile.name) {
            showNotification('정책 파일을 선택해주세요.', 'error');
            return;
        }
        
        if (!vendor) {
            showNotification('방화벽 벤더를 선택해주세요.', 'error');
            return;
        }
        
        // 워크플로우 ID가 없으면 새로 생성
        if (!workflowState.workflowId) {
            startNewWorkflow();
            setTimeout(() => submitInitializeForm(formData), 500);
        } else {
            submitInitializeForm(formData);
        }
    }
    
    function submitInitializeForm(formData) {
        // 상태 업데이트
        updateStepStatus('initialized', 'processing');
        showModal('정책 파일 초기화 중...');
        
        // API 호출
        fetch('/api/policy_manager/initialize', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStepStatus('initialized', 'completed');
                workflowState.steps.initialized = true;
                
                // 다음 단계 활성화
                requestForm.querySelector('button').disabled = false;
                
                // 결과 업데이트
                updateResults(data.files);
                showNotification('정책 파일 초기화 완료', 'success');
            } else {
                updateStepStatus('initialized', 'failed');
                showNotification('초기화 실패: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('초기화 오류:', error);
            updateStepStatus('initialized', 'failed');
            showNotification('초기화 중 오류가 발생했습니다.', 'error');
        })
        .finally(() => {
            closeModal();
        });
    }

    /**
     * 신청 정보 처리 단계
     */
    function handleRequestProcess(event) {
        event.preventDefault();
        
        const formData = new FormData(requestForm);
        formData.append('workflow_id', workflowState.workflowId);
        
        // 상태 업데이트
        updateStepStatus('request_processed', 'processing');
        showModal('신청 정보 처리 중...');
        
        // API 호출
        fetch('/api/policy_manager/process_request', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStepStatus('request_processed', 'completed');
                workflowState.steps.request_processed = true;
                
                // 다음 단계 활성화
                usageForm.querySelector('button').disabled = false;
                
                // 결과 업데이트
                updateResults(data.files);
                showNotification('신청 정보 처리 완료', 'success');
            } else {
                updateStepStatus('request_processed', 'failed');
                showNotification('신청 정보 처리 실패: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('신청 정보 처리 오류:', error);
            updateStepStatus('request_processed', 'failed');
            showNotification('신청 정보 처리 중 오류가 발생했습니다.', 'error');
        })
        .finally(() => {
            closeModal();
        });
    }

    /**
     * 사용 데이터 처리 단계
     */
    function handleUsageProcess(event) {
        event.preventDefault();
        
        const formData = new FormData(usageForm);
        formData.append('workflow_id', workflowState.workflowId);
        
        // 상태 업데이트
        updateStepStatus('usage_processed', 'processing');
        showModal('사용 데이터 처리 중...');
        
        // API 호출
        fetch('/api/policy_manager/process_usage', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStepStatus('usage_processed', 'completed');
                workflowState.steps.usage_processed = true;
                
                // 다음 단계 활성화
                vendorProcessBtn.disabled = false;
                
                // 결과 업데이트
                updateResults(data.files);
                showNotification('사용 데이터 처리 완료', 'success');
            } else {
                updateStepStatus('usage_processed', 'failed');
                showNotification('사용 데이터 처리 실패: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('사용 데이터 처리 오류:', error);
            updateStepStatus('usage_processed', 'failed');
            showNotification('사용 데이터 처리 중 오류가 발생했습니다.', 'error');
        })
        .finally(() => {
            closeModal();
        });
    }

    /**
     * 벤더별 처리 단계
     */
    function handleVendorProcess() {
        // 상태 업데이트
        updateStepStatus('vendor_processed', 'processing');
        showModal('벤더별 처리 중...');
        
        // API 호출
        fetch('/api/policy_manager/process_vendor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                workflow_id: workflowState.workflowId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStepStatus('vendor_processed', 'completed');
                workflowState.steps.vendor_processed = true;
                
                // 다음 단계 활성화
                duplicateAnalysisBtn.disabled = false;
                
                // 결과 업데이트
                updateResults(data.files);
                showNotification('벤더별 처리 완료', 'success');
            } else {
                updateStepStatus('vendor_processed', 'failed');
                showNotification('벤더별 처리 실패: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('벤더별 처리 오류:', error);
            updateStepStatus('vendor_processed', 'failed');
            showNotification('벤더별 처리 중 오류가 발생했습니다.', 'error');
        })
        .finally(() => {
            closeModal();
        });
    }

    /**
     * 중복 정책 분석 단계
     */
    function handleDuplicateAnalysis() {
        // 상태 업데이트
        updateStepStatus('duplicates_analyzed', 'processing');
        showModal('중복 정책 분석 중...');
        
        // API 호출
        fetch('/api/policy_manager/analyze_duplicates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                workflow_id: workflowState.workflowId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStepStatus('duplicates_analyzed', 'completed');
                workflowState.steps.duplicates_analyzed = true;
                
                // 다음 단계 활성화
                generateReportsBtn.disabled = false;
                
                // 결과 업데이트
                updateResults(data.files);
                showNotification('중복 정책 분석 완료', 'success');
            } else {
                updateStepStatus('duplicates_analyzed', 'failed');
                showNotification('중복 정책 분석 실패: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('중복 정책 분석 오류:', error);
            updateStepStatus('duplicates_analyzed', 'failed');
            showNotification('중복 정책 분석 중 오류가 발생했습니다.', 'error');
        })
        .finally(() => {
            closeModal();
        });
    }

    /**
     * 보고서 생성 단계
     */
    function handleReportGeneration() {
        // 상태 업데이트
        updateStepStatus('reports_generated', 'processing');
        showModal('보고서 생성 중...');
        
        // API 호출
        fetch('/api/policy_manager/generate_reports', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                workflow_id: workflowState.workflowId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateStepStatus('reports_generated', 'completed');
                workflowState.steps.reports_generated = true;
                
                // 다운로드 버튼 활성화
                downloadAllBtn.disabled = false;
                
                // 결과 업데이트
                updateResults(data.files);
                showNotification('보고서 생성 완료', 'success');
            } else {
                updateStepStatus('reports_generated', 'failed');
                showNotification('보고서 생성 실패: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('보고서 생성 오류:', error);
            updateStepStatus('reports_generated', 'failed');
            showNotification('보고서 생성 중 오류가 발생했습니다.', 'error');
        })
        .finally(() => {
            closeModal();
        });
    }

    /**
     * 모든 파일 다운로드
     */
    function handleDownloadAll() {
        // API 호출
        fetch('/api/policy_manager/download_all', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                workflow_id: workflowState.workflowId
            })
        })
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('다운로드 실패');
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `policy_analysis_${workflowState.workflowId}.zip`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            showNotification('모든 파일 다운로드 완료', 'success');
        })
        .catch(error => {
            console.error('다운로드 오류:', error);
            showNotification('파일 다운로드 중 오류가 발생했습니다.', 'error');
        });
    }

    /**
     * 개별 파일 다운로드
     */
    function handleFileDownload(fileId) {
        window.location.href = `/api/policy_manager/download_file/${fileId}`;
    }

    /**
     * 워크플로우 상태 초기화
     */
    function resetWorkflowState() {
        workflowState.workflowId = null;
        workflowState.currentStep = null;
        
        Object.keys(workflowState.steps).forEach(step => {
            workflowState.steps[step] = false;
            updateStepStatus(step, 'pending');
        });
        
        workflowState.files = {
            intermediate: [],
            reports: []
        };
        
        // UI 초기화
        requestForm.querySelector('button').disabled = true;
        usageForm.querySelector('button').disabled = true;
        vendorProcessBtn.disabled = true;
        duplicateAnalysisBtn.disabled = true;
        generateReportsBtn.disabled = true;
        downloadAllBtn.disabled = true;
        
        noResults.style.display = 'block';
        resultsFiles.style.display = 'none';
    }

    /**
     * 단계 상태 업데이트
     */
    function updateStepStatus(step, status) {
        const stepCard = document.querySelector(`.step-card[data-step="${step}"]`);
        if (!stepCard) return;
        
        const statusElement = stepCard.querySelector('.step-status');
        if (!statusElement) return;
        
        // 이전 상태 클래스 제거
        statusElement.classList.remove('pending', 'processing', 'completed', 'failed');
        
        // 새 상태 클래스 추가
        statusElement.classList.add(status);
        
        // 상태 텍스트 업데이트
        const statusTexts = {
            pending: '대기중',
            processing: '처리중',
            completed: '완료',
            failed: '실패'
        };
        
        statusElement.textContent = statusTexts[status] || status;
    }

    /**
     * 결과 파일 목록 업데이트
     */
    function updateResults(files) {
        if (!files) return;
        
        // 파일 목록 저장
        if (files.intermediate) {
            workflowState.files.intermediate = files.intermediate;
        }
        
        if (files.reports) {
            workflowState.files.reports = files.reports;
        }
        
        // 중간 결과 파일 목록 업데이트
        if (intermediateFilesList && files.intermediate) {
            intermediateFilesList.innerHTML = '';
            
            files.intermediate.forEach(file => {
                const li = document.createElement('li');
                
                const nameSpan = document.createElement('span');
                nameSpan.className = 'file-name';
                nameSpan.textContent = file.name;
                
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'file-actions';
                
                const downloadBtn = document.createElement('button');
                downloadBtn.className = 'btn btn-secondary';
                downloadBtn.textContent = '다운로드';
                downloadBtn.addEventListener('click', () => handleFileDownload(file.id));
                
                actionsDiv.appendChild(downloadBtn);
                li.appendChild(nameSpan);
                li.appendChild(actionsDiv);
                
                intermediateFilesList.appendChild(li);
            });
        }
        
        // 보고서 파일 목록 업데이트
        if (reportFilesList && files.reports) {
            reportFilesList.innerHTML = '';
            
            files.reports.forEach(file => {
                const li = document.createElement('li');
                
                const nameSpan = document.createElement('span');
                nameSpan.className = 'file-name';
                nameSpan.textContent = file.name;
                
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'file-actions';
                
                const downloadBtn = document.createElement('button');
                downloadBtn.className = 'btn btn-secondary';
                downloadBtn.textContent = '다운로드';
                downloadBtn.addEventListener('click', () => handleFileDownload(file.id));
                
                actionsDiv.appendChild(downloadBtn);
                li.appendChild(nameSpan);
                li.appendChild(actionsDiv);
                
                reportFilesList.appendChild(li);
            });
        }
        
        // 결과 섹션 표시
        if ((files.intermediate && files.intermediate.length > 0) || 
            (files.reports && files.reports.length > 0)) {
            noResults.style.display = 'none';
            resultsFiles.style.display = 'block';
        }
    }

    /**
     * 모달 표시
     */
    function showModal(message) {
        statusMessage.textContent = message || '처리 중...';
        updateProgress(0);
        modal.classList.add('show');
    }

    /**
     * 모달 닫기
     */
    function closeModal() {
        modal.classList.remove('show');
    }

    /**
     * 진행률 업데이트
     */
    function updateProgress(percent) {
        progressFill.style.width = `${percent}%`;
        progressText.textContent = `${percent}%`;
    }

    /**
     * 알림 표시
     */
    function showNotification(message, type = 'info') {
        const notificationContainer = document.getElementById('notificationContainer');
        if (!notificationContainer) return;
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        notificationContainer.appendChild(notification);
        
        // 5초 후 자동 제거
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notificationContainer.removeChild(notification);
            }, 300);
        }, 5000);
    }

    // 페이지 로드 시 워크플로우 상태 초기화
    resetWorkflowState();
}); 