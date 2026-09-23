
// =====================================================
// GOOGLE TRANSLATE
// =====================================================

function googleTranslateElementInit() {

    new google.translate.TranslateElement(
        {
            pageLanguage: "en",
            includedLanguages: "en,hi",
            autoDisplay: false
        },
        "google_translate_element"
    );

}


// =====================================================
// FIXMYCITY LANGUAGE SWITCHER
// =====================================================

function toggleLanguageMenu(event) {
    event.stopPropagation();

    const menu = document.getElementById("languageMenu");
    if (!menu) return;

    menu.classList.toggle("show");
}

// Close dropdown when clicking anywhere outside it
document.addEventListener("click", function (event) {
    const menu = document.getElementById("languageMenu");
    const switcher = document.querySelector(".language-switcher");

    if (menu && switcher && !switcher.contains(event.target)) {
        menu.classList.remove("show");
    }
});

function setGoogTransCookie(langCode) {
    const value = "/en/" + langCode;
    document.cookie = "googtrans=" + value + "; path=/";
    document.cookie = "googtrans=" + value + "; path=/; domain=" + window.location.hostname;
}

function clearGoogTransCookie() {
    document.cookie = "googtrans=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC";
    document.cookie = "googtrans=; path=/; domain=" + window.location.hostname + "; expires=Thu, 01 Jan 1970 00:00:00 UTC";
}

function updateSelectedLanguageLabel(langCode) {
    const label = document.getElementById("selectedLanguage");
    if (label) {
        label.textContent = langCode === "hi" ? "हिन्दी" : "English";
    }
}

function selectLanguage(langCode) {
    localStorage.setItem("fixmycity_lang", langCode);
    updateSelectedLanguageLabel(langCode);

    const menu = document.getElementById("languageMenu");
    if (menu) menu.classList.remove("show");

    if (langCode === "en") {
        clearGoogTransCookie();
        window.location.reload();
        return;
    }

    setGoogTransCookie(langCode);

    // If Google's hidden select is already on the page, trigger it directly
    // (avoids a reload when possible).
    const combo = document.querySelector("select.goog-te-combo");

    if (combo) {
        combo.value = langCode;
        combo.dispatchEvent(new Event("change"));
    } else {
        window.location.reload();
    }
}

// Restore language choice on every page load (Django re-renders base.html
// fresh on each navigation, so this keeps the selection consistent site-wide)
(function applyStoredLanguage() {
    const savedLang = localStorage.getItem("fixmycity_lang") || "en";

    updateSelectedLanguageLabel(savedLang);

    if (savedLang === "hi") {
        setGoogTransCookie(savedLang);
    }
})();