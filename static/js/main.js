document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const btnClear = document.getElementById('btn-clear');
    const suggestions = document.getElementById('suggestions');
    const modal = document.getElementById('modal');
    const passInput = document.getElementById('pass-input');
    const btnConfirm = document.getElementById('btn-confirm');
    const btnCancel = document.getElementById('btn-cancel');
    const downloadArea = document.getElementById('download-area');
    const selectedNameEl = document.getElementById('selected-name');
    const fileLinksEl = document.getElementById('file-links');
    const previewOverlay = document.getElementById('preview-overlay');
    const btnClosePreview = document.getElementById('btn-close-preview');
    const previewFrame = document.getElementById('preview-frame');
    const previewTitle = document.getElementById('preview-title');

    // Comment Functionality
    const commentModal   = document.getElementById('comment-modal');
    const btnOpenComment = document.getElementById('btn-open-comment');
    const btnCancelComment = document.getElementById('btn-cancel-comment');
    const btnSubmitComment = document.getElementById('btn-submit-comment');
    const commentInput   = document.getElementById('comment-input');

    if (btnOpenComment) {
        btnOpenComment.addEventListener('click', () => {
            if (commentModal) commentModal.style.display = 'flex';
            if (commentInput) { commentInput.value = ''; commentInput.focus(); }
        });
    }

    if (btnCancelComment) {
        btnCancelComment.addEventListener('click', () => {
            if (commentModal) commentModal.style.display = 'none';
        });
    }

    if (btnSubmitComment) {
        btnSubmitComment.addEventListener('click', async () => {
            const comment = commentInput ? commentInput.value.trim() : '';
            if (!comment) return;

            btnSubmitComment.disabled = true;
            btnSubmitComment.innerHTML = '<i class="fas fa-spinner fa-spin"></i> กำลังส่ง...';

            try {
                const response = await fetch('/api/comment', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        fullName: selectedPerson ? selectedPerson.fullName : '',
                        comment: comment
                    })
                });
                const data = await response.json();
                if (data.success) {
                    alert('ส่งข้อความเรียบร้อยแล้ว ขอบคุณสำหรับข้อมูลครับ');
                    if (commentModal) commentModal.style.display = 'none';
                } else {
                    alert('เกิดข้อผิดพลาด: ' + data.message);
                }
            } catch (error) {
                alert('ไม่สามารถเชื่อมต่อกับเซิร์ฟเวอร์ได้');
            } finally {
                btnSubmitComment.disabled = false;
                btnSubmitComment.innerHTML = '<i class="fas fa-paper-plane"></i> ส่งข้อความ';
            }
        });
    }

    let allPeople = [];
    let selectedPerson = null;

    // Fetch list of people
    async function fetchPeople() {
        try {
            const response = await fetch('/api/people');
            const data = await response.json();
            if (Array.isArray(data)) {
                allPeople = data;
                console.log(`Loaded ${allPeople.length} people.`);
            } else {
                console.error('API returned non-array data:', data);
                allPeople = [];
            }
        } catch (error) {
            console.error('Error fetching people:', error);
            allPeople = [];
        }
    }

    // Helper to normalize Thai names for searching
    function normalizeThai(text) {
        if (!text) return "";
        return text.replace(/นนร\./g, "")
                   .replace(/น\.น\.ร\./g, "")
                   .replace(/น\.น\.ร/g, "")
                   .replace(/\s+/g, "")
                   .replace(/\./g, "")
                   .toLowerCase()
                   .trim();
    }

    // Search and Suggest
    searchInput.addEventListener('input', (e) => {
        const rawQuery = e.target.value.trim();
        const query = normalizeThai(rawQuery);
        
        // Show/Hide Clear Button
        btnClear.style.display = rawQuery.length > 0 ? 'block' : 'none';

        if (rawQuery.length < 1) {
            suggestions.style.display = 'none';
            return;
        }

        const filtered = allPeople.filter(p => {
            const normalizedName = normalizeThai(p.name);
            return normalizedName.includes(query);
        }).slice(0, 10);

        if (filtered.length > 0) {
            suggestions.innerHTML = filtered.map(p => `
                <div class="suggestion-item" data-fullname="${p.fullName}" data-name="${p.name}">
                    ${p.name}
                </div>
            `).join('');
            suggestions.style.display = 'block';
        } else {
            suggestions.style.display = 'none';
        }
    });

    // Clear Search
    btnClear.addEventListener('click', () => {
        searchInput.value = '';
        btnClear.style.display = 'none';
        suggestions.style.display = 'none';
        downloadArea.style.display = 'none';
        previewOverlay.style.display = 'none';
        selectedPerson = null;
        searchInput.focus();
    });

    // Handle suggestion click
    suggestions.addEventListener('click', (e) => {
        const item = e.target.closest('.suggestion-item');
        if (!item) return;

        selectedPerson = {
            fullName: item.dataset.fullname,
            name: item.dataset.name
        };

        searchInput.value = selectedPerson.name;
        suggestions.style.display = 'none';
        
        // Open Modal
        modal.style.display = 'flex';
        passInput.value = '';
        passInput.focus();
    });

    // Close password modal
    btnCancel.addEventListener('click', () => {
        modal.style.display = 'none';
        selectedPerson = null;
        if (searchInput.value === '') btnClear.style.display = 'none';
    });

    // Verify Password and Show Downloads
    btnConfirm.addEventListener('click', async () => {
        const password = passInput.value.trim();
        if (!password) return;

        try {
            const response = await fetch('/api/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fullName: selectedPerson.fullName,
                    password: password
                })
            });

            const data = await response.json();

            if (data.success) {
                modal.style.display = 'none';
                renderDownloads(selectedPerson, data.files, password);
            } else {
                alert(data.message || 'รหัสไม่ถูกต้อง');
            }
        } catch (error) {
            alert('เกิดข้อผิดพลาดในการตรวจสอบ');
        }
    });

    function renderDownloads(person, files, password) {
        selectedNameEl.textContent = person.name;
        
        const pdfFile = files.find(f => f.toLowerCase().endsWith('.pdf'));
        const docxFile = files.find(f => f.toLowerCase().endsWith('.docx'));

        let html = '';
        
        if (pdfFile) {
            html += `
                <div style="margin-bottom: 1rem; display: flex; gap: 0.5rem; justify-content: center;">
                    <button class="btn btn-download btn-preview" onclick="showPreview('${encodeURIComponent(person.fullName)}', '${encodeURIComponent(pdfFile)}', '${password}')">
                        <i class="fas fa-eye"></i> ดูตัวอย่าง PDF
                    </button>
                    <button onclick="downloadFile('${encodeURIComponent(person.fullName)}', '${encodeURIComponent(pdfFile)}', '${password}', this)" class="btn-download btn-pdf">
                        <i class="fas fa-file-pdf"></i> ดาวน์โหลด PDF
                    </button>
                </div>
            `;
        }

        if (docxFile) {
            html += `
                <div style="display: flex; gap: 0.5rem; justify-content: center;">
                    <button onclick="downloadFile('${encodeURIComponent(person.fullName)}', '${encodeURIComponent(docxFile)}', '${password}', this)" class="btn-download btn-docx">
                        <i class="fas fa-file-word"></i> ดาวน์โหลด DOCX
                    </button>
                </div>
            `;
        }

        fileLinksEl.innerHTML = html;
        downloadArea.style.display = 'block';
        downloadArea.scrollIntoView({ behavior: 'smooth' });

        // แสดงปุ่ม comment หลัง verify สำเร็จ
        if (btnOpenComment) btnOpenComment.style.display = 'flex';
    }

    // Preview handling
    window.showPreview = (folder, filename, password) => {
        const url = `/preview/${folder}/${filename}?pass=${password}`;
        previewTitle.textContent = `ตัวอย่างไฟล์: ${decodeURIComponent(filename)}`;
        previewFrame.src = url;
        previewOverlay.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent scrolling
    };

    btnClosePreview.addEventListener('click', () => {
        previewOverlay.style.display = 'none';
        previewFrame.src = '';
        document.body.style.overflow = 'auto';
    });

    // Download with Animation handling
    window.downloadFile = async (folder, filename, password, btnElement) => {
        const originalContent = btnElement.innerHTML;
        const decodedFilename = decodeURIComponent(filename);
        
        // Show loading animation
        btnElement.innerHTML = `<i class="fas fa-spinner fa-spin"></i> กำลังโหลด...`;
        btnElement.style.opacity = '0.7';
        btnElement.style.pointerEvents = 'none';

        try {
            const url = `/download/${folder}/${filename}?pass=${password}`;
            const response = await fetch(url);
            
            if (!response.ok) throw new Error('Download failed');
            
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = downloadUrl;
            a.download = decodedFilename;
            
            document.body.appendChild(a);
            a.click();
            
            window.URL.revokeObjectURL(downloadUrl);
            a.remove();
        } catch (error) {
            alert('เกิดข้อผิดพลาดในการดาวน์โหลด: ' + error.message);
        } finally {
            // Restore button
            btnElement.innerHTML = originalContent;
            btnElement.style.opacity = '1';
            btnElement.style.pointerEvents = 'auto';
        }
    };

    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            suggestions.style.display = 'none';
        }
    });

    fetchPeople();
});