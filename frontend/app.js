// API Base URL
const API_BASE = 'http://127.0.0.1:8000';

// Socket.IO connection
const token = localStorage.getItem('access_token');
const socket = io(API_BASE, token ? { auth: { token: `Bearer ${token}` } } : {});

function redirectToLogin() {
    try { localStorage.removeItem('access_token'); } catch {}
    showAlert('Session expired. Redirecting to staff login...', 'error');
    setTimeout(() => { window.location.href = '/staff'; }, 1000);
}

function renderAuthControls() {
    const container = document.getElementById('authControls');
    if (!container) return;
    if (token) {
        container.innerHTML = `<button class="btn btn-secondary" id="logoutBtn"><i class="fas fa-sign-out-alt"></i> Logout</button>`;
        const btn = document.getElementById('logoutBtn');
        btn && btn.addEventListener('click', () => {
            try { localStorage.removeItem('access_token'); } catch {}
            window.location.href = '/staff';
        });
    } else {
        container.innerHTML = `<a class="btn btn-secondary" href="/staff"><i class="fas fa-sign-in-alt"></i> Staff Login</a>`;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const isStaff = !!token;

    renderAuthControls();

    // Toggle UI based on role
    const submitBtn = document.getElementById('submitTabBtn');
    const dashboardBtn = document.getElementById('dashboardTabBtn');
    const urgentBtn = document.getElementById('urgentTabBtn');
    const analyticsBtn = document.getElementById('analyticsTabBtn');

    const submitTabEl = document.getElementById('submitTab');
    const dashboardTabEl = document.getElementById('dashboardTab');
    const urgentTabEl = document.getElementById('urgentTab');
    const analyticsTabEl = document.getElementById('analyticsTab');

    if (isStaff) {
        // Hide patient form for staff
        if (submitBtn) submitBtn.style.display = 'none';
        if (submitTabEl) submitTabEl.style.display = 'none';

        // Ensure a staff tab is active
        dashboardBtn && dashboardBtn.classList.add('active');
        dashboardTabEl && dashboardTabEl.classList.add('active');
        // Remove active from submit if present
        submitBtn && submitBtn.classList.remove('active');
        submitTabEl && submitTabEl.classList.remove('active');
    } else {
        // Hide staff tabs for patients
        if (dashboardBtn) dashboardBtn.style.display = 'none';
        if (urgentBtn) urgentBtn.style.display = 'none';
        if (analyticsBtn) analyticsBtn.style.display = 'none';
        if (dashboardTabEl) dashboardTabEl.style.display = 'none';
        if (urgentTabEl) urgentTabEl.style.display = 'none';
        if (analyticsTabEl) analyticsTabEl.style.display = 'none';

        // Ensure submit is active
        submitBtn && submitBtn.classList.add('active');
        submitTabEl && submitTabEl.classList.add('active');
    }

    // Set default visit date to today
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('visitDate').value = now.toISOString().slice(0, 16);

    // Load initial data
    if (document.getElementById('dashboardTab').classList.contains('active')) {
        loadFeedback();
    }
    if (document.getElementById('analyticsTab').classList.contains('active')) {
        loadAnalytics();
    }

    // Socket.IO event listeners
    socket.on('connect', () => {
        console.log('Connected to server');
        showAlert('Connected to real-time updates', 'success');
    });

    socket.on('new_feedback', (data) => {
        showAlert(`New feedback received from ${data.department}`, 'info');
        if (document.getElementById('dashboardTab').classList.contains('active')) {
            loadFeedback();
        }
    });

    socket.on('urgent_alert', (data) => {
        showCriticalAlert(data);
        showAlert(`🚨 URGENT: Critical feedback from ${data.department} - ${data.urgency_reason}`, 'error');
        if (document.getElementById('dashboardTab').classList.contains('active')) {
            loadFeedback();
        }
    });

    socket.on('analysis_complete', (data) => {
        showAlert(`Analysis complete for feedback #${data.feedback_id}`, 'success');
        if (document.getElementById('dashboardTab').classList.contains('active')) {
            loadFeedback();
        }
    });
});

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName + 'Tab').classList.add('active');
    event.target.closest('.tab-btn').classList.add('active');

    // Load data if needed
    if (tabName === 'dashboard') {
        loadFeedback();
    } else if (tabName === 'analytics') {
        loadAnalytics();
    }
}

// Rating display
function updateRatingDisplay(value) {
    document.getElementById('ratingValue').textContent = value;
    const stars = '★'.repeat(value) + '☆'.repeat(5 - value);
    document.getElementById('starsDisplay').textContent = stars;
}

// Form submission
document.getElementById('feedbackForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = {
        patient_name: document.getElementById('patientName').value || null,
        visit_date: document.getElementById('visitDate').value,
        department: document.getElementById('department').value,
        doctor_name: document.getElementById('doctorName').value || null,
        feedback_text: document.getElementById('feedbackText').value,
        rating: parseInt(document.getElementById('rating').value)
    };

    try {
        const response = await fetch(`${API_BASE}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const data = await response.json();
            // Show confirmation page
            showConfirmation();
        } else {
            const error = await response.json();
            showAlert(`Error: ${error.detail || 'Failed to submit feedback'}`, 'error');
        }
    } catch (error) {
        showAlert(`Error: ${error.message}`, 'error');
    }
});

// Show confirmation page
function showConfirmation() {
    document.getElementById('feedbackFormContainer').style.display = 'none';
    document.getElementById('confirmationMessage').style.display = 'block';
}

// Reset form
function resetForm() {
    document.getElementById('feedbackForm').reset();
    document.getElementById('confirmationMessage').style.display = 'none';
    document.getElementById('feedbackFormContainer').style.display = 'block';
    updateRatingDisplay(3);
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('visitDate').value = now.toISOString().slice(0, 16);
}

// Load feedback list (table format)
async function loadFeedback() {
    const tableBody = document.getElementById('feedbackTableBody');
    tableBody.innerHTML = '<tr><td colspan="9" class="loading">Loading feedback...</td></tr>';

    const department = document.getElementById('filterDepartment')?.value || '';
    const status = document.getElementById('filterStatus')?.value || '';
    const urgency = document.getElementById('filterUrgency')?.value || '';

    try {
        let url = `${API_BASE}/feedback/all?limit=100`;
        if (department) url += `&department=${encodeURIComponent(department)}`;
        if (status) url += `&status=${encodeURIComponent(status)}`;
        if (urgency) url += `&priority=${encodeURIComponent(urgency)}`;

        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const response = await fetch(url, { headers });
        const data = await response.json();
        if (response.status === 401) {
            return redirectToLogin();
        }

        if (data.feedbacks && data.feedbacks.length > 0) {
            tableBody.innerHTML = '';
            let criticalCount = 0;
            let pendingCount = 0;

            data.feedbacks.forEach(feedback => {
                const row = createFeedbackTableRow(feedback);
                tableBody.appendChild(row);
                if (feedback.urgency === 'critical') criticalCount++;
                if (feedback.status === 'pending_analysis') pendingCount++;
            });

            // Update stats
            document.getElementById('totalCount').textContent = data.total || data.feedbacks.length;
            document.getElementById('criticalCount').textContent = criticalCount;
            document.getElementById('pendingCount').textContent = pendingCount;
        } else {
            tableBody.innerHTML = '<tr><td colspan="9" class="loading">No feedback found</td></tr>';
        }
    } catch (error) {
        tableBody.innerHTML = `<tr><td colspan="9" class="loading">Error loading feedback: ${error.message}</td></tr>`;
    }
}

// Create table row for feedback
function createFeedbackTableRow(feedback) {
    const row = document.createElement('tr');
    if (feedback.urgency === 'critical') {
        row.classList.add('critical-row');
    }

    const feedbackPreview = feedback.feedback_text.length > 100 
        ? feedback.feedback_text.substring(0, 100) + '...' 
        : feedback.feedback_text;

    row.innerHTML = `
        <td>#${feedback.id}</td>
        <td>${feedback.patient_name || 'Anonymous'}</td>
        <td>${feedback.department}</td>
        <td>${feedbackPreview}</td>
        <td>
            <span class="badge">${feedback.rating}/5</span>
        </td>
        <td>
            <span class="badge">${feedback.status || 'pending'}</span>
        </td>
        <td>
            ${feedback.sentiment ? `<span class="badge ${feedback.sentiment}">${feedback.sentiment}</span>` : 
              feedback.analysis_status === 'pending' ? '<span class="badge" style="background: #fef3c7; color: #92400e;">Analyzing...</span>' : '-'}
        </td>
        <td>
            ${feedback.urgency ? `<span class="badge ${feedback.urgency}">${feedback.urgency}</span>` : 
              feedback.analysis_status === 'pending' ? '<span class="badge" style="background: #fef3c7; color: #92400e;">Analyzing...</span>' : '-'}
        </td>
        <td>
            <div class="action-buttons">
                <button class="btn btn-small btn-view" onclick="viewFeedback(${feedback.id})">
                    <i class="fas fa-eye"></i> View
                </button>
                <button class="btn btn-small btn-action" onclick="openActionModal(${feedback.id})">
                    <i class="fas fa-tasks"></i> Action
                </button>
            </div>
        </td>
    `;

    return row;
}

// Load urgent feedback
async function loadUrgentFeedback() {
    const container = document.getElementById('urgentFeedbackList');
    container.innerHTML = '<div class="loading">Loading urgent feedback...</div>';

    try {
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const response = await fetch(`${API_BASE}/feedback/urgent?limit=100`, { headers });
        const data = await response.json();
        if (response.status === 401) {
            return redirectToLogin();
        }

        if (data.urgent_feedbacks && data.urgent_feedbacks.length > 0) {
            container.innerHTML = '';
            data.urgent_feedbacks.forEach(feedback => {
                const item = createUrgentFeedbackItem(feedback);
                container.appendChild(item);
            });
        } else {
            container.innerHTML = '<div class="loading">No urgent feedback found</div>';
        }
    } catch (error) {
        container.innerHTML = `<div class="loading">Error loading urgent feedback: ${error.message}</div>`;
    }
}

// Create urgent feedback item
function createUrgentFeedbackItem(feedback) {
    const item = document.createElement('div');
    item.className = 'feedback-item critical';

    const flags = feedback.urgency_flags && feedback.urgency_flags.length > 0
        ? feedback.urgency_flags.map(flag => `<span class="badge critical">${flag}</span>`).join(' ')
        : '';

    item.innerHTML = `
        <div class="feedback-header">
            <div>
                <h3>🚨 Critical: ${feedback.patient_name || 'Anonymous'} - ${feedback.department}</h3>
                <div class="feedback-meta">
                    <span class="badge critical">CRITICAL</span>
                    ${feedback.sentiment ? `<span class="badge ${feedback.sentiment}">${feedback.sentiment}</span>` : ''}
                    <span class="badge">Rating: ${feedback.rating}/5</span>
                    ${flags}
                </div>
            </div>
        </div>
        <div class="feedback-text">
            <strong>Urgency Reason:</strong> ${feedback.urgency_reason || 'Not specified'}<br><br>
            <strong>Feedback:</strong> ${feedback.feedback_text}
        </div>
        ${feedback.actionable_insights ? `
            <div style="margin-top: 15px; padding: 15px; background: #fef3c7; border-radius: 8px;">
                <strong>Actionable Insights:</strong> ${feedback.actionable_insights}
            </div>
        ` : ''}
        <div class="feedback-footer">
            <span><i class="fas fa-calendar"></i> ${new Date(feedback.visit_date).toLocaleDateString()}</span>
            <span><i class="fas fa-user-md"></i> ${feedback.doctor_name || 'N/A'}</span>
            <span><i class="fas fa-tag"></i> ${feedback.primary_category || 'Uncategorized'}</span>
            <div class="action-buttons">
                <button class="btn btn-small btn-view" onclick="viewFeedback(${feedback.id})">
                    <i class="fas fa-eye"></i> View Details
                </button>
                <button class="btn btn-small btn-action" onclick="openActionModal(${feedback.id})">
                    <i class="fas fa-tasks"></i> Take Action
                </button>
            </div>
        </div>
    `;

    return item;
}

// Show critical alert banner
function showCriticalAlert(data) {
    const container = document.getElementById('criticalAlerts');
    const alert = document.createElement('div');
    alert.className = 'critical-alert-banner';
    alert.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <div class="critical-alert-content">
            <h3>🚨 Critical Feedback Alert</h3>
            <p><strong>${data.feedback_preview}</strong></p>
            <p>Department: ${data.department} | Reason: ${data.urgency_reason}</p>
        </div>
        <button class="btn btn-secondary" onclick="viewFeedback(${data.feedback_id})">
            View Details
        </button>
    `;
    container.appendChild(alert);
    
    // Auto remove after 10 seconds
    setTimeout(() => {
        alert.remove();
    }, 10000);
}

// Open action modal
function openActionModal(feedbackId) {
    document.getElementById('actionFeedbackId').value = feedbackId;
    document.getElementById('actionModal').style.display = 'block';
}

// Close action modal
function closeActionModal() {
    document.getElementById('actionModal').style.display = 'none';
    document.getElementById('actionForm').reset();
}

// Handle action form submission
document.getElementById('actionForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const feedbackId = document.getElementById('actionFeedbackId').value;
    const status = document.getElementById('actionStatus').value;
    const staffNote = document.getElementById('staffNote').value;
    const assignedDepartment = document.getElementById('assignedDepartment').value;

    try {
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const response = await fetch(`${API_BASE}/feedback/${feedbackId}/update`, {
            method: 'POST',
            headers,
            body: JSON.stringify({
                status: status,
                staff_note: staffNote || null,
                assigned_department: assignedDepartment || null
            })
        });

        if (response.ok) {
            showAlert('Action saved successfully!', 'success');
            closeActionModal();
            loadFeedback();
        } else {
            const error = await response.json();
            if (response.status === 401) return redirectToLogin();
            showAlert(`Error: ${error.detail || 'Failed to save action'}`, 'error');
        }
    } catch (error) {
        showAlert(`Error: ${error.message}`, 'error');
    }
});

// View feedback details
async function viewFeedback(id) {
    try {
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const response = await fetch(`${API_BASE}/feedback/${id}`, { headers });
        const feedback = await response.json();
        if (response.status === 401) {
            return redirectToLogin();
        }

        const modal = document.getElementById('feedbackModal');
        const modalBody = document.getElementById('modalBody');

        let analysisHtml = '';
        if (feedback.analysis) {
            const a = feedback.analysis;
            analysisHtml = `
                <div class="analytics-section">
                    <h3>AI Analysis</h3>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-icon ${a.sentiment === 'positive' ? 'positive' : a.sentiment === 'negative' ? 'negative' : ''}">
                                <i class="fas fa-brain"></i>
                            </div>
                            <div class="stat-info">
                                <h3>${a.sentiment}</h3>
                                <p>Sentiment (${(a.confidence_score * 100).toFixed(0)}% confidence)</p>
                            </div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon ${a.urgency === 'critical' ? 'critical' : ''}">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                            <div class="stat-info">
                                <h3>${a.urgency}</h3>
                                <p>Urgency Level</p>
                            </div>
                        </div>
                    </div>
                    ${a.urgency_reason ? `<p><strong>Urgency Reason:</strong> ${a.urgency_reason}</p>` : ''}
                    ${a.actionable_insights ? `<p><strong>Actionable Insights:</strong> ${a.actionable_insights}</p>` : ''}
                    ${a.key_points && a.key_points.length > 0 ? `
                        <h4>Key Points:</h4>
                        <ul>
                            ${a.key_points.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            `;
        }

        modalBody.innerHTML = `
            <h2>Feedback Details #${feedback.id}</h2>
            <div class="card">
                <p><strong>Patient:</strong> ${feedback.patient_name || 'Anonymous'}</p>
                <p><strong>Department:</strong> ${feedback.department}</p>
                <p><strong>Doctor:</strong> ${feedback.doctor_name || 'N/A'}</p>
                <p><strong>Visit Date:</strong> ${new Date(feedback.visit_date).toLocaleString()}</p>
                <p><strong>Rating:</strong> ${feedback.rating}/5</p>
                <p><strong>Status:</strong> ${feedback.status}</p>
                <h3>Feedback:</h3>
                <p>${feedback.feedback_text}</p>
            </div>
            ${analysisHtml}
        `;

        modal.style.display = 'block';
    } catch (error) {
        showAlert(`Error loading feedback: ${error.message}`, 'error');
    }
}

// Close modal
function closeModal() {
    document.getElementById('feedbackModal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const feedbackModal = document.getElementById('feedbackModal');
    const actionModal = document.getElementById('actionModal');
    if (event.target === feedbackModal) {
        feedbackModal.style.display = 'none';
    }
    if (event.target === actionModal) {
        actionModal.style.display = 'none';
    }
}

// Load analytics
async function loadAnalytics() {
    try {
        const headers = {};
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const [summaryResponse, trendsResponse] = await Promise.all([
            fetch(`${API_BASE}/analytics/summary`, { headers }),
            fetch(`${API_BASE}/analytics/trends`, { headers })
        ]);
        if (summaryResponse.status === 401 || trendsResponse.status === 401) return redirectToLogin();

        const summary = await summaryResponse.json();
        const trends = await trendsResponse.json();

        // Update stats
        document.getElementById('totalFeedback').textContent = summary.total_feedback || 0;
        document.getElementById('positiveCount').textContent = summary.sentiment_breakdown?.positive || 0;
        document.getElementById('negativeCount').textContent = summary.sentiment_breakdown?.negative || 0;
        
        // Calculate critical count (would need to filter from trends or add to summary)
        document.getElementById('criticalCount').textContent = 'N/A';

        // Department ratings
        const deptContainer = document.getElementById('departmentRatings');
        if (summary.department_ratings && summary.department_ratings.length > 0) {
            deptContainer.innerHTML = summary.department_ratings.map(dept => `
                <div class="department-item">
                    <div>
                        <strong>${dept.department}</strong>
                        <p>${dept.feedback_count} feedback(s)</p>
                    </div>
                    <div>
                        <strong>${dept.average_rating.toFixed(1)}</strong>
                        <p>Average Rating</p>
                    </div>
                </div>
            `).join('');
        } else {
            deptContainer.innerHTML = '<p>No department data available</p>';
        }

        // Top issues
        const issuesContainer = document.getElementById('topIssues');
        if (summary.top_issues && summary.top_issues.length > 0) {
            issuesContainer.innerHTML = summary.top_issues.map(issue => `
                <div class="issue-item">
                    <span>${issue.category}</span>
                    <span class="badge">${issue.count} occurrences</span>
                </div>
            `).join('');
        } else {
            issuesContainer.innerHTML = '<p>No issues data available</p>';
        }
    } catch (error) {
        console.error('Error loading analytics:', error);
        showAlert(`Error loading analytics: ${error.message}`, 'error');
    }
}

// Show alert
function showAlert(message, type = 'info') {
    const container = document.getElementById('alertContainer');
    const alert = document.createElement('div');
    alert.className = `alert ${type}`;
    alert.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Initialize rating display
updateRatingDisplay(3);

