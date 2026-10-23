/* Phase 9: GSAP motion is progressive enhancement; the site works without it. */
(() => {
  const revealTargets = document.querySelectorAll('.hero-copy, .hero-art, .trust-row > div, .section-head, .place-card, .explore-card, .community-intro, .feed-panel, .detail-hero, .review-card');
  if (window.gsap && revealTargets.length) {
    window.gsap.fromTo(revealTargets, { y: 16, opacity: 0 }, {
      y: 0, opacity: 1, duration: 0.55, stagger: 0.055, ease: 'power2.out', clearProps: 'all'
    });
  }
  const currentYear = document.querySelectorAll('[data-current-year]');
  currentYear.forEach((node) => { node.textContent = new Date().getFullYear(); });
})();
