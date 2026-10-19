/**
 * Tola Motion System
 * Source: docs/03-DESIGN-SYSTEM.md section 3.7
 * Easing: cubic-bezier(0.22, 1, 0.36, 1)
 * Uses GSAP, ScrollTrigger, and Lenis from CDN
 */

(function () {
  "use strict";

  // 1. Accessibility: Strictly respect prefers-reduced-motion
  const prefersMotion = window.matchMedia("(prefers-reduced-motion: no-preference)").matches;
  if (!prefersMotion) {
    return;
  }

  // 2. Initialize smooth scroll via Lenis (Public pages only, NEVER on inspection form)
  const isInspectionForm = document.getElementById("inspection-form") !== null;
  let lenisInstance = null;

  if (!isInspectionForm && typeof Lenis !== "undefined") {
    lenisInstance = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    });

    if (typeof ScrollTrigger !== "undefined" && typeof gsap !== "undefined") {
      lenisInstance.on("scroll", ScrollTrigger.update);
      gsap.ticker.add((time) => {
        lenisInstance.raf(time * 1000);
      });
      gsap.ticker.lagSmoothing(0);
    } else {
      function raf(time) {
        lenisInstance.raf(time);
        requestAnimationFrame(raf);
      }
      requestAnimationFrame(raf);
    }
  }

  // 3. Nav Rail Scroll Hide / Return
  const navRail = document.querySelector(".nav-rail");
  if (navRail) {
    let lastScrollY = window.scrollY;
    const threshold = 8;

    window.addEventListener(
      "scroll",
      () => {
        const currentScrollY = window.scrollY;
        const delta = currentScrollY - lastScrollY;

        if (currentScrollY < 32) {
          navRail.classList.remove("nav-rail--hidden");
        } else if (delta > threshold) {
          // Scrolling down
          navRail.classList.add("nav-rail--hidden");
        } else if (delta < -threshold) {
          // Scrolling up
          navRail.classList.remove("nav-rail--hidden");
        }
        lastScrollY = currentScrollY;
      },
      { passive: true }
    );
  }

  // Ensure GSAP and ScrollTrigger are loaded before running entrance animations
  if (typeof gsap === "undefined") {
    return;
  }

  if (typeof ScrollTrigger !== "undefined") {
    gsap.registerPlugin(ScrollTrigger);
  }

  // 4. Hero Headline Line-Mask Reveal with 90ms stagger
  const heroLines = document.querySelectorAll(".hero-title .line-text");
  if (heroLines.length > 0) {
    gsap.from(heroLines, {
      y: "115%",
      duration: 0.75,
      stagger: 0.09, // Exactly 90 ms stagger per specification
      ease: "power3.out",
      clearProps: "transform",
    });
  }

  // 5. Section Reveals (Fade and rise 24 px, once, at 80% viewport height)
  if (typeof ScrollTrigger !== "undefined") {
    const revealSections = document.querySelectorAll(".landing-section, .reveal-on-scroll");
    revealSections.forEach((section) => {
      gsap.from(section, {
        y: 24,
        opacity: 0,
        duration: 0.65,
        ease: "power2.out",
        clearProps: "transform,opacity",
        scrollTrigger: {
          trigger: section,
          start: "top 80%",
          once: true,
        },
      });
    });

    // 6. Stat Counters Counting Up Once When Visible
    const counters = document.querySelectorAll(".stat-counter");
    counters.forEach((el) => {
      const target = parseFloat(el.dataset.target) || 0;
      const decimals = parseInt(el.dataset.decimals, 10) || 0;
      const suffix = el.dataset.suffix || "";

      ScrollTrigger.create({
        trigger: el,
        start: "top 85%",
        once: true,
        onEnter: () => {
          const counterObj = { val: 0 };
          gsap.to(counterObj, {
            val: target,
            duration: 1.3,
            ease: "power2.out",
            onUpdate: () => {
              el.textContent = counterObj.val.toFixed(decimals) + suffix;
            },
            onComplete: () => {
              el.textContent = target.toFixed(decimals) + suffix;
            },
          });
        },
      });
    });
  }
})();
