document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const hamburger = document.querySelector('.hamburger');
    const navbarNav = document.querySelector('.navbar-nav');
    
    if (hamburger) {
        hamburger.addEventListener('click', function() {
            navbarNav.classList.toggle('show');
        });
    }
    
    // Search functionality
    const searchForm = document.querySelector('#searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const query = document.querySelector('#searchInput').value.trim();
            if (query) {
                window.location.href = `/search?query=${encodeURIComponent(query)}`;
            }
        });
    }
    
    // Filter buttons
    const filterButtons = document.querySelectorAll('.filter-button');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Si le bouton a un attribut href, utiliser celui-ci
            if (this.getAttribute('href') && !this.getAttribute('href').startsWith('#')) {
                return; // L'action par défaut du navigateur prendra le relais
            }
            
            // Sinon, utiliser l'attribut data-genre
            const genre = this.dataset.genre;
            if (genre) {
                window.location.href = `/search?genre=${encodeURIComponent(genre)}`;
            }
            
            // Pour les liens d'ancre internes
            if (this.getAttribute('href') && this.getAttribute('href').startsWith('#')) {
                const targetId = this.getAttribute('href').substring(1);
                const targetElement = document.getElementById(targetId);
                
                if (targetElement) {
                    // Ajouter une classe active au bouton cliqué
                    filterButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Scroll avec animation
                    targetElement.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'start'
                    });
                }
            }
        });
    });
    
    // Seasons tabs
    const seasonTabs = document.querySelectorAll('.season-tab');
    const seasonContents = document.querySelectorAll('.season-content');
    
    if (seasonTabs.length > 0) {
        seasonTabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const seasonId = this.dataset.season;
                
                // Remove active class from all tabs and hide all content
                seasonTabs.forEach(t => t.classList.remove('active'));
                seasonContents.forEach(c => c.style.display = 'none');
                
                // Add active class to clicked tab and show corresponding content
                this.classList.add('active');
                document.querySelector(`.season-content[data-season="${seasonId}"]`).style.display = 'block';
            });
        });
        
        // Activate the first tab by default
        seasonTabs[0].click();
    }
    
    // Handle download button click
    const downloadButton = document.querySelector('a[download]');
    if (downloadButton) {
        downloadButton.addEventListener('click', function(e) {
            // Log that download was clicked for debugging
            console.log('Download button clicked, URL:', this.href);
            
            // Make sure the URL is a direct download link from Google Drive
            if (this.href.includes('drive.google.com')) {
                console.log('Processing Google Drive download');
                // The download attribute should help trigger the download
                // The browser will handle the rest
            }
        });
    }
    
    // Animation on scroll
    if ('IntersectionObserver' in window) {
        const fadeElements = document.querySelectorAll('.fade-in');
        const fadeObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    fadeObserver.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1
        });
        
        fadeElements.forEach(element => {
            fadeObserver.observe(element);
        });
    }
});