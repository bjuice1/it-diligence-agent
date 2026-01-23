/**
 * Staffing Tree View JavaScript
 * Handles expand/collapse, filtering, and highlighting
 */

// Toggle category expansion
function toggleCategory(categoryName) {
    const category = document.querySelector(`[data-category="${categoryName}"]`);
    if (category) {
        category.classList.toggle('expanded');
    }
}

// Toggle role expansion
function toggleRole(categoryName, roleIndex) {
    const content = document.getElementById(`content-${categoryName}-${roleIndex}`);
    if (content) {
        const role = content.parentElement;
        role.classList.toggle('expanded');
    }
}

// Expand all categories and roles
function expandAll() {
    document.querySelectorAll('.tree-category').forEach(cat => {
        cat.classList.add('expanded');
    });
    document.querySelectorAll('.tree-role').forEach(role => {
        role.classList.add('expanded');
    });
}

// Collapse all categories and roles
function collapseAll() {
    document.querySelectorAll('.tree-category').forEach(cat => {
        cat.classList.remove('expanded');
    });
    document.querySelectorAll('.tree-role').forEach(role => {
        role.classList.remove('expanded');
    });
}

// Filter by entity (target/buyer/all)
function filterByEntity(entity) {
    document.querySelectorAll('.tree-person').forEach(person => {
        const personEntity = person.dataset.entity;
        if (entity === 'all' || personEntity === entity) {
            person.classList.remove('hidden');
        } else {
            person.classList.add('hidden');
        }
    });
    updateCounts();
}

// Toggle key person highlighting
function toggleKeyPersonHighlight(enabled) {
    document.querySelectorAll('.tree-person.key-person').forEach(person => {
        if (enabled) {
            person.style.background = '';
        } else {
            person.style.background = 'transparent';
        }
    });
}

// Update visible counts after filtering
function updateCounts() {
    document.querySelectorAll('.tree-category').forEach(category => {
        const visible = category.querySelectorAll('.tree-person:not(.hidden)').length;
        const countSpan = category.querySelector('.category-count');
        if (countSpan) {
            countSpan.textContent = `(${visible})`;
        }
    });

    document.querySelectorAll('.tree-role').forEach(role => {
        const visible = role.querySelectorAll('.tree-person:not(.hidden)').length;
        const countSpan = role.querySelector('.role-count');
        if (countSpan) {
            countSpan.textContent = `(${visible})`;
        }
    });
}

// MSP card toggle
function toggleMSP(mspId) {
    const card = document.querySelector(`[data-msp="${mspId}"]`);
    if (card) {
        card.classList.toggle('expanded');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Expand first category by default
    const firstCategory = document.querySelector('.tree-category');
    if (firstCategory) {
        firstCategory.classList.add('expanded');
    }
});
