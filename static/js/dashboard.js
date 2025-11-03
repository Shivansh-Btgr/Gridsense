// Dashboard animations
document.addEventListener('DOMContentLoaded', () => {
    // Animate stat cards on load
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Animate feature cards
    const featureCards = document.querySelectorAll('.dashboard-feature-card');
    featureCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 300 + index * 100);
    });

    // Counter animation for stats
    const animateCounter = (element, target) => {
        let current = 0;
        const increment = target / 50;
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = target;
                clearInterval(timer);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 20);
    };

    // Example: Animate accuracy percentage
    const accuracyElement = document.querySelector('.stat-card-content h3');
    if (accuracyElement && accuracyElement.textContent === '99%') {
        accuracyElement.textContent = '0%';
        setTimeout(() => {
            let current = 0;
            const timer = setInterval(() => {
                current += 1;
                if (current >= 99) {
                    accuracyElement.textContent = '99%';
                    clearInterval(timer);
                } else {
                    accuracyElement.textContent = current + '%';
                }
            }, 20);
        }, 1000);
    }
});

// Mobile sidebar toggle (for responsive design)
const toggleSidebar = () => {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('active');
};
