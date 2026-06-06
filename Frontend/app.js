document.addEventListener('DOMContentLoaded', () => {
    // --- Navigation (Sidebar) ---
    const navBtns = document.querySelectorAll('.nav-btn');
    const viewPages = document.querySelectorAll('.view-page');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all nav buttons and views
            navBtns.forEach(b => b.classList.remove('active'));
            viewPages.forEach(p => p.classList.remove('active-view'));

            // Add active class to clicked button and target view
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active-view');
        });
    });

    // --- File Handling & Search for both Views ---
    setupViewLogic('mfcc');
    setupViewLogic('birdnet');

    function setupViewLogic(methodId) {
        const view = document.getElementById(`view-${methodId}`);
        const dropZone = view.querySelector('.drop-zone');
        const audioUpload = view.querySelector('.audio-upload');
        const uploadContent = view.querySelector('.upload-content');
        const fileInfo = view.querySelector('.file-info');
        const fileName = view.querySelector('.file-name');
        const removeFileBtn = view.querySelector('.remove-file');
        const searchBtn = view.querySelector('.search-btn');
        
        const resultsSection = view.querySelector('.results-section');
        const resultsList = view.querySelector('.results-list');
        const loader = view.querySelector('.loader-container');
        const latencyBadge = view.querySelector('.latency-badge');

        let currentFile = null;

        // Drag and Drop
        dropZone.addEventListener('click', (e) => {
            if(e.target !== removeFileBtn && !e.target.closest('.remove-file')) {
                audioUpload.click();
            }
        });

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                handleFile(e.dataTransfer.files[0]);
            }
        });

        audioUpload.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });

        removeFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            resetFile();
        });

        function handleFile(file) {
            if (file.type.startsWith('audio/') || file.name.endsWith('.wav') || file.name.endsWith('.mp3')) {
                currentFile = file;
                fileName.textContent = file.name;
                uploadContent.classList.add('hidden');
                fileInfo.classList.remove('hidden');
                searchBtn.disabled = false;
            } else {
                alert('Vui lòng chọn tệp âm thanh hợp lệ (.wav, .mp3)');
            }
        }

        function resetFile() {
            currentFile = null;
            audioUpload.value = '';
            uploadContent.classList.remove('hidden');
            fileInfo.classList.add('hidden');
            searchBtn.disabled = true;
            resultsSection.classList.add('hidden');
        }

        // Search Action
        searchBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            if (!currentFile) return;

            // UI Transition
            resultsSection.classList.add('hidden');
            loader.classList.remove('hidden');
            searchBtn.disabled = true;

            try {
                // Gọi API thực tế tới Backend Flask
                const formData = new FormData();
                formData.append('query_audio', currentFile);
                formData.append('method', methodId);
                const response = await fetch('http://localhost:5000/search', { method: 'POST', body: formData });
                
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || "Lỗi xử lý từ máy chủ");
                }
                
                const data = await response.json();
                
                renderResults(data, methodId, resultsList);
                
                // Hiển thị thời gian chi tiết cho BirdNET
                if (methodId === 'birdnet' && data.extraction_time_ms !== undefined) {
                    latencyBadge.innerHTML = `
                        <i class="fa-solid fa-bolt"></i> AI: ${data.extraction_time_ms}ms 
                        | <i class="fa-solid fa-database"></i> DB: ${data.search_time_ms}ms 
                        | Tổng: ${data.latency}ms
                    `;
                } else {
                    latencyBadge.textContent = `Tốc độ: ${data.latency}ms`;
                }
                
            } catch (error) {
                alert('Có lỗi xảy ra khi tìm kiếm: ' + error.message);
            } finally {
                loader.classList.add('hidden');
                resultsSection.classList.remove('hidden');
                searchBtn.disabled = false;
            }
        });
    }

    function generateMockResults(methodId) {
        const latency = methodId === 'mfcc' ? 
            Math.floor(Math.random() * 20) + 10 :  // 10-30ms for MFCC
            Math.floor(Math.random() * 50) + 150;  // 150-200ms for BirdNET

        const results = [];
        const speciesNames = methodId === 'mfcc' 
            ? ["Passer montanus", "Pycnonotus jocosus", "Copsychus saularis", "Passer rutilans", "Pycnonotus blanfordi"]
            : ["Passer montanus", "Passer domesticus", "Pycnonotus jocosus", "Dicrurus macrocercus", "Copsychus saularis"];
            
        const commonNames = methodId === 'mfcc'
            ? ["Sẻ đồng", "Chào mào", "Chích chòe than", "Sẻ hung", "Chào mào bông"]
            : ["Sẻ đồng", "Sẻ nhà", "Chào mào", "Chèo bẻo", "Chích chòe than"];

        for (let i = 0; i < 5; i++) {
            const baseSimilarity = methodId === 'birdnet' ? 96 - (i * 2) : 89 - (i * 3);
            const similarity = (baseSimilarity + Math.random() * 2).toFixed(1);
            
            results.push({
                id: `XC${Math.floor(Math.random() * 90000) + 10000}`,
                species: speciesNames[i],
                common_name: commonNames[i],
                similarity: similarity,
                audio_url: `https://xeno-canto.org/sounds/uploaded/mock_audio_${i}.mp3` // mock url
            });
        }

        return { latency, results };
    }

    function renderResults(data, methodId, resultsList) {
        resultsList.innerHTML = '';
        const scoreClass = `score-${methodId}`;
        const metricName = methodId === 'mfcc' ? 'Độ tương đồng (MFCC)' : 'Độ tương đồng (AI)';
        
        // Xử lý trường hợp không có kết quả
        if (!data.results || data.results.length === 0) {
            resultsList.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-circle-exclamation"></i>
                    <p>Không tìm thấy kết quả phù hợp.</p>
                </div>
            `;
            return;
        }
        
        data.results.forEach((item, index) => {
            // Thanh tiến trình cho BirdNET 
            const progressBar = methodId === 'birdnet' ? `
                <div class="similarity-bar">
                    <div class="similarity-fill" style="width: ${Math.max(0, Math.min(100, item.similarity))}%; transition: width 0.8s ease ${index * 0.15}s;"></div>
                </div>
            ` : '';
            
            const resultHtml = `
                <div class="result-item" style="animation: slideIn 0.3s ease forwards ${index * 0.1}s; opacity: 0; transform: translateY(20px);">
                    <div class="result-rank">#${index + 1}</div>
                    <div class="result-info">
                        <h4>${item.common_name} <i>(${item.species})</i></h4>
                        <div class="result-meta">
                            <span>Mã: ${item.id}</span>
                            <span class="${scoreClass}"><i class="fa-solid fa-chart-simple"></i> ${metricName}: ${item.similarity}%</span>
                        </div>
                        ${progressBar}
                    </div>
                    <div class="result-audio">
                        <audio controls controlsList="nodownload">
                            <source src="${item.audio_url}" type="audio/mpeg">
                            Trình duyệt của bạn không hỗ trợ thẻ audio.
                        </audio>
                    </div>
                </div>
            `;
            resultsList.insertAdjacentHTML('beforeend', resultHtml);
        });
    }

    // Add keyframes for animation dynamically if not present
    if (!document.getElementById('dynamic-styles')) {
        const style = document.createElement('style');
        style.id = 'dynamic-styles';
        style.innerHTML = `
            @keyframes slideIn {
                to { opacity: 1; transform: translateY(0); }
            }
        `;
        document.head.appendChild(style);
    }
});
