// Simple interactivity for the e-commerce site
document.addEventListener('DOMContentLoaded', function() {
    // Menu button functionality
    const menuBtn = document.querySelector('.menu-btn');
    if (menuBtn) {
        menuBtn.addEventListener('click', function() {
            alert('Menu functionality would open here!');
            // Add your menu opening logic here
        });
    }

    // Navigation smooth scrolling
    const navLinks = document.querySelectorAll('.nav-menu a');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                // Add smooth scroll functionality here
                console.log('Navigating to:', targetId);
            }
        });
    });

    // Add hover effects to cards
    const cards = document.querySelectorAll('.contact-card, .welcome-card, .nav-card, .product-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Simple animation on load
    const animateOnLoad = () => {
        const elements = document.querySelectorAll('.contact-card, .welcome-card, .nav-card, .product-card');
        elements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                element.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, index * 100);
        });
    };

    animateOnLoad();
});

// Additional functionality can be added here for:
// - Shopping cart
// - Product filtering
// - Form validation
// - Payment processing