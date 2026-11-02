const navToggle = document.querySelector(".nav-toggle");
const siteNav = document.querySelector(".site-nav");

const sitePath = window.location.pathname;
const siteRoot = sitePath.includes("/tools/") ? "../../" : sitePath.includes("/events/") || sitePath.includes("/weekly-highlights/") || sitePath.includes("/contact/") || sitePath.includes("/AIP_Diagnosis/") ? "../" : "";
const pageType = sitePath.includes("/events/") ? "event" : sitePath.includes("/weekly-highlights/") ? "highlight" : sitePath.includes("/contact/") ? "contact" : "home";

if (siteNav) {
  const navItems = [
    ["Home", `${siteRoot}index.html#home`, pageType === "home"],
    ["Highlight", `${siteRoot}weekly-highlights/weekly-highlight-2026-11-01.html`, pageType === "highlight"],
    ["Event", pageType === "event" ? "index.html" : `${siteRoot}events/index.html`, pageType === "event"],
    ["Contact", `${siteRoot}index.html#contact`, pageType === "contact"],
  ];

  siteNav.replaceChildren(...navItems.map(([label, href, active]) => {
    const link = document.createElement("a");
    link.href = href;
    link.textContent = label;
    if (active) {
      link.classList.add("active");
      link.setAttribute("aria-current", "page");
    }
    return link;
  }));
}

const header = document.querySelector(".site-header");
if (header && !header.querySelector(".header-instagram")) {
  const instagram = document.createElement("a");
  instagram.className = "header-instagram";
  instagram.href = "https://www.instagram.com/tokai_pancreatobiliary_team/";
  instagram.target = "_blank";
  instagram.rel = "noopener";
  instagram.setAttribute("aria-label", "胆膵班Instagramを開く");
  instagram.title = "胆膵班Instagram";
  instagram.innerHTML = `<img class="header-instagram-icon" src="${siteRoot}assets/instagram-icon.png" alt=""><span>Instagram</span>`;
  header.append(instagram);
}

const navLinks = document.querySelectorAll(".site-nav a");
const year = document.querySelector("#year");
const backToTop = document.querySelector(".back-to-top");

if (year) {
  year.textContent = new Date().getFullYear();
}

if (navToggle && siteNav) {
  navToggle.addEventListener("click", () => {
    const isOpen = siteNav.classList.toggle("open");
    navToggle.setAttribute("aria-expanded", String(isOpen));
    navToggle.setAttribute("aria-label", isOpen ? "メニューを閉じる" : "メニューを開く");
  });
}

navLinks.forEach((link) => {
  link.addEventListener("click", () => {
    siteNav.classList.remove("open");
    navToggle.setAttribute("aria-expanded", "false");
    navToggle.setAttribute("aria-label", "メニューを開く");
  });
});

const sections = [...document.querySelectorAll("main section[id]")];

const updateActiveNav = () => {
  let current = null;

  sections.forEach((section) => {
    if (section.getBoundingClientRect().top <= 120) {
      current = section;
    }
  });

  navLinks.forEach((link) => {
    const href = link.getAttribute("href");
    if (href?.startsWith("#")) {
      link.classList.toggle("active", current && href === `#${current.id}`);
    }
  });
};

window.addEventListener("scroll", updateActiveNav, { passive: true });
window.addEventListener("load", updateActiveNav);

if (backToTop) {
  backToTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

document.querySelectorAll("[data-lightbox-target]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = document.getElementById(button.dataset.lightboxTarget);

    if (!target) return;

    target.classList.add("open");
    target.setAttribute("aria-hidden", "false");
    document.body.classList.add("lightbox-active");
  });
});

document.querySelectorAll(".lightbox").forEach((lightbox) => {
  const close = () => {
    lightbox.classList.remove("open");
    lightbox.setAttribute("aria-hidden", "true");
    document.body.classList.remove("lightbox-active");
  };

  lightbox.querySelector(".lightbox-close")?.addEventListener("click", close);
  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) close();
  });
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;

  document.querySelectorAll(".lightbox.open").forEach((lightbox) => {
    lightbox.classList.remove("open");
    lightbox.setAttribute("aria-hidden", "true");
  });
  document.body.classList.remove("lightbox-active");
});
