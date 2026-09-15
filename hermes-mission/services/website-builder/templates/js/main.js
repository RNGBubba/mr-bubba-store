/**
 * Mr Bubba Data Services - Website Template JS
 * Mobile menu, scroll animations, contact form handling
 */
(function() {
    'use strict';

    // Mobile menu toggle
    const mobileToggle = document.querySelector('.mobile-toggle');
    const nav = document.querySelector('.nav');
    if (mobileToggle && nav) {
        mobileToggle.addEventListener('click', function() {
            nav.classList.toggle('active');
            const icon = this.querySelector('i');
            if (nav.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });

        // Close menu on link click
        nav.querySelectorAll('a').forEach(function(link) {
            link.addEventListener('click', function() {
                nav.classList.remove('active');
                mobileToggle.querySelector('i').classList.remove('fa-times');
                mobileToggle.querySelector('i').classList.add('fa-bars');
            });
        });
    }

    // Header scroll effect
    var header = document.querySelector('.header');
    if (header) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        });
    }

    // Intersection Observer for animations
    if ('IntersectionObserver' in window) {
        var observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

        document.querySelectorAll('.service-card, .testimonial-card, .value-card, .team-card, .portfolio-item, .process-step, .service-detail').forEach(function(el) {
            observer.observe(el);
        });
    }

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
        anchor.addEventListener('click', function(e) {
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                var offset = header ? header.offsetHeight : 0;
                var top = target.getBoundingClientRect().top + window.pageYOffset - offset;
                window.scrollTo({ top: top, behavior: 'smooth' });
            }
        });
    });

    // Contact form submission (static site — uses mailto fallback)
    var contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            var name = document.getElementById('name').value;
            var email = document.getElementById('email').value;
            var phone = document.getElementById('phone').value || 'Not provided';
            var service = document.getElementById('service').value || 'General inquiry';
            var message = document.getElementById('message').value;

            // Build mailto link (works without backend)
            var subject = 'Website Inquiry: ' + service;
            var body = 'Name: ' + name + '%0D%0A';
            body += 'Email: ' + email + '%0D%0A';
            body += 'Phone: ' + phone + '%0D%0A';
            body += 'Service: ' + service + '%0D%0A%0D%0A';
            body += 'Message:%0D%0A' + message;

            var mailtoLink = 'mailto:' + contactForm.closest('.contact-page')
                ? document.querySelector('.contact-item a[href^="mailto:"]')?.href.replace('mailto:', '') || ''
                : '' + '?subject=' + encodeURIComponent(subject) + '&body=' + body;

            // Fallback: show success message
            contactForm.innerHTML = '<div style="text-align:center;padding:40px;">' +
                '<i class="fas fa-check-circle" style="color:#e8a838;font-size:3rem;margin-bottom:16px;display:block;"></i>' +
                '<h3 style="color:#1e3a5f;margin-bottom:8px;">Message Sent!</h3>' +
                '<p>Thank you for reaching out. We\'ll get back to you within 24 hours.</p>' +
                '</div>';

            // Also attempt mailto
            window.location.href = 'mailto:' + (document.querySelector('a[href^="mailto:"]')?.href.replace('mailto:', '') || '') +
                '?subject=' + encodeURIComponent(subject) + '&body=' + body;
        });
    }

    // Portfolio filter
    var filterBtns = document.querySelectorAll('.filter-btn');
    var portfolioItems = document.querySelectorAll('.portfolio-item');
    if (filterBtns.length && portfolioItems.length) {
        filterBtns.forEach(function(btn) {
            btn.addEventListener('click', function() {
                filterBtns.forEach(function(b) { b.classList.remove('active'); });
                this.classList.add('active');
                var filter = this.getAttribute('data-filter');
                portfolioItems.forEach(function(item) {
                    if (filter === 'all' || item.getAttribute('data-category') === filter) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }
})();
