// =====================================================
// CITIZEN REGISTRATION
// =====================================================

const registerForm = document.querySelector(".login-form");

if (
    registerForm &&
    (
        window.location.pathname.includes("register.html") ||
        window.location.pathname.includes("/register/")
    )
) {

    registerForm.addEventListener("submit", async function (event) {

        event.preventDefault();

        const formData = new FormData(registerForm);

        const password = formData.get("password");
        const confirmPassword = formData.get("confirm_password");

        // Check password
        if (password !== confirmPassword) {
            alert("Passwords do not match.");
            return;
        }

        try {

            const response = await fetch(
                "http://127.0.0.1:8000/api/register/",
                {
                    method: "POST",
                    body: formData
                }
            );

            const data = await response.json();

            if (data.success) {

                alert(
                    "Account created successfully!\n\n" +
                    "Your Citizen ID: " +
                    data.citizen_id
                );

                window.location.href = "login.html";

            } else {

                alert(data.message);
            }

        } catch (error) {

            console.error("Registration Error:", error);

            alert(
                "Unable to connect to server.\n" +
                "Please make sure Django server is running."
            );
        }

    });
}

function googleTranslateElementInit() {
    new google.translate.TranslateElement(
        {
            pageLanguage: 'en',
            includedLanguages: 'en,hi',
            autoDisplay: false
        },
        'google_translate_element'
    );
}

/* =====================================================
   FIXMYCITY LANGUAGE SYSTEM
===================================================== */

const translations = {

    en: {

        logo: "FixMyCity",

        nav_home: "Home",
        nav_issues: "Issues",
        nav_how: "How It Works",
        nav_about: "About",

        who_are_you: "Who are you?",
        report_issue: "Report an Issue",
        explore_issues: "Explore Issues",

        hero_tag: "Civic Issue Reporting Platform",
        hero_title_1: "Together, Let's",
        hero_title_2: "Fix Our City.",

        hero_description:
            "Report civic problems, help your community, and track the progress of issues that matter. Make your city cleaner, safer and better.",

        issues_reported: "Issues Reported",
        issues_resolved: "Issues Resolved",
        resolution_rate: "Resolution Rate",

        city_issue_map: "City Issue Map",
        live_civic_activity: "Live civic activity",
        live: "LIVE",

        road_damage: "Road Damage",
        pothole_reported: "Pothole reported",

        garbage_overflow: "Garbage Overflow",
        community_reported: "Community reported",

        streetlight: "Streetlight",
        needs_attention: "Needs attention",

        water_leakage: "Water Leakage",
        new_report: "New report",

        nearby_issues: "Nearby Issues",
        garbage: "Garbage",
        streetlights: "Streetlights",
        water_issues: "Water Issues",

        city_status: "CITY STATUS",
        monitoring_active: "Monitoring active",
        issues_tracked: "Civic issues are being tracked",

        resolved_today: "Resolved Today",
        community_upvotes: "Community Upvotes",

        road: "Road",
        lighting: "Lighting",

        access_portal: "Access Portal",
        select_role:
            "Select your role to continue to the FixMyCity portal.",

        citizen: "Citizen",

        citizen_description:
            "Report civic issues, upload photos, share locations and upvote problems reported by your community.",

        citizen_login: "Citizen Login",

        new_citizen: "New citizen?",
        create_account: "Create account",

        officer: "Officer",

        officer_description:
            "View assigned complaints, update issue status and manage civic problems within your department.",

        officer_login: "Officer Login",

        admin: "Admin",

        admin_description:
            "Manage users, officers, departments and monitor the complete civic issue reporting system.",

        admin_login: "Admin Login",

        report_anything: "Report Anything",

        city_problem:
            "What's happening in your city?",

        report_common_problems:
            "Report common civic problems and help authorities take action faster.",

        road_description:
            "Report potholes, damaged roads, broken sidewalks and unsafe streets.",

        garbage_description:
            "Report overflowing garbage bins, waste dumping and sanitation issues.",

        broken_streetlights:
            "Broken Streetlights",

        streetlight_description:
            "Report streetlights that are broken, damaged or not functioning.",

        water_description:
            "Report water leakage, pipeline damage and other water-related problems.",

        simple_process: "Simple Process",

        report_to_resolution:
            "From report to resolution.",

        simple_transparent:
            "FixMyCity makes civic issue reporting simple, transparent and community-driven.",

        report: "Report",

        report_step:
            "Capture a photo, select the issue category, describe the problem and mark its exact location on the map.",

        upvote: "Upvote",

        upvote_step:
            "Find existing nearby complaints and upvote them instead of creating duplicate reports.",

        track: "Track",

        track_step:
            "Follow your complaint as it moves from Reported to In Progress and finally to Resolved.",

        about_fixmycity: "About FixMyCity",

        better_reporting:
            "Better reporting. Better cities.",

        about_description:
            "FixMyCity connects citizens and civic authorities through one transparent platform for reporting and resolving everyday city problems.",

        see_something:
            "See something broken?",

        cta_description:
            "Don't just ignore it. Report it, let your community support it, and help get it fixed.",

        footer_tagline:
            "Building better cities together."
    },


    hi: {

        logo: "FixMyCity",

        nav_home: "होम",
        nav_issues: "समस्याएँ",
        nav_how: "यह कैसे काम करता है",
        nav_about: "हमारे बारे में",

        who_are_you: "आप कौन हैं?",
        report_issue: "समस्या रिपोर्ट करें",
        explore_issues: "समस्याएँ देखें",

        hero_tag: "नागरिक समस्या रिपोर्टिंग प्लेटफ़ॉर्म",

        hero_title_1: "आइए मिलकर",
        hero_title_2: "अपने शहर को बेहतर बनाएं।",

        hero_description:
            "नागरिक समस्याओं की रिपोर्ट करें, अपने समुदाय की मदद करें और महत्वपूर्ण समस्याओं की प्रगति को ट्रैक करें। अपने शहर को स्वच्छ, सुरक्षित और बेहतर बनाएं।",

        issues_reported: "रिपोर्ट की गई समस्याएँ",
        issues_resolved: "हल की गई समस्याएँ",
        resolution_rate: "समाधान दर",

        city_issue_map: "शहर की समस्या का नक्शा",
        live_civic_activity: "लाइव नागरिक गतिविधि",
        live: "लाइव",

        road_damage: "सड़क की समस्या",
        pothole_reported: "गड्ढे की रिपोर्ट",

        garbage_overflow: "कचरे का ओवरफ्लो",
        community_reported: "समुदाय द्वारा रिपोर्ट",

        streetlight: "स्ट्रीट लाइट",
        needs_attention: "ध्यान देने की आवश्यकता",

        water_leakage: "पानी का रिसाव",
        new_report: "नई रिपोर्ट",

        nearby_issues: "पास की समस्याएँ",
        garbage: "कचरा",
        streetlights: "स्ट्रीट लाइट्स",
        water_issues: "पानी की समस्याएँ",

        city_status: "शहर की स्थिति",
        monitoring_active: "निगरानी सक्रिय है",
        issues_tracked: "नागरिक समस्याओं की निगरानी की जा रही है",

        resolved_today: "आज हल की गई समस्याएँ",
        community_upvotes: "समुदाय के अपवोट",

        road: "सड़क",
        lighting: "लाइटिंग",

        access_portal: "पोर्टल एक्सेस",

        select_role:
            "FixMyCity पोर्टल पर आगे बढ़ने के लिए अपनी भूमिका चुनें।",

        citizen: "नागरिक",

        citizen_description:
            "नागरिक समस्याओं की रिपोर्ट करें, फोटो अपलोड करें, स्थान साझा करें और अपने समुदाय द्वारा रिपोर्ट की गई समस्याओं को अपवोट करें।",

        citizen_login: "नागरिक लॉगिन",

        new_citizen: "नए नागरिक हैं?",
        create_account: "अकाउंट बनाएं",

        officer: "अधिकारी",

        officer_description:
            "सौंपी गई शिकायतें देखें, समस्या की स्थिति अपडेट करें और अपने विभाग की नागरिक समस्याओं को प्रबंधित करें।",

        officer_login: "अधिकारी लॉगिन",

        admin: "एडमिन",

        admin_description:
            "यूज़र्स, अधिकारियों और विभागों को मैनेज करें तथा पूरे नागरिक समस्या रिपोर्टिंग सिस्टम की निगरानी करें।",

        admin_login: "एडमिन लॉगिन",

        report_anything: "किसी भी समस्या की रिपोर्ट करें",

        city_problem:
            "आपके शहर में क्या हो रहा है?",

        report_common_problems:
            "आम नागरिक समस्याओं की रिपोर्ट करें और अधिकारियों को तेजी से कार्रवाई करने में मदद करें।",

        road_description:
            "गड्ढों, खराब सड़कों, टूटे फुटपाथ और असुरक्षित सड़कों की रिपोर्ट करें।",

        garbage_description:
            "भरे हुए कचरे के डिब्बों, कचरा फेंकने और स्वच्छता संबंधी समस्याओं की रिपोर्ट करें।",

        broken_streetlights:
            "खराब स्ट्रीट लाइट्स",

        streetlight_description:
            "खराब, टूटी या काम न करने वाली स्ट्रीट लाइट्स की रिपोर्ट करें।",

        water_description:
            "पानी के रिसाव, पाइपलाइन की खराबी और पानी से संबंधित अन्य समस्याओं की रिपोर्ट करें।",

        simple_process: "सरल प्रक्रिया",

        report_to_resolution:
            "रिपोर्ट से समाधान तक।",

        simple_transparent:
            "FixMyCity नागरिक समस्या रिपोर्टिंग को सरल, पारदर्शी और समुदाय-आधारित बनाता है।",

        report: "रिपोर्ट करें",

        report_step:
            "फोटो लें, समस्या की श्रेणी चुनें, समस्या का विवरण दें और नक्शे पर उसका सही स्थान चिन्हित करें।",

        upvote: "अपवोट करें",

        upvote_step:
            "पास की मौजूदा शिकायतों को खोजें और नई डुप्लीकेट रिपोर्ट बनाने के बजाय उन्हें अपवोट करें।",

        track: "ट्रैक करें",

        track_step:
            "अपनी शिकायत को Reported से In Progress और अंत में Resolved होने तक ट्रैक करें।",

        about_fixmycity:
            "FixMyCity के बारे में",

        better_reporting:
            "बेहतर रिपोर्टिंग। बेहतर शहर।",

        about_description:
            "FixMyCity नागरिकों और नागरिक अधिकारियों को एक पारदर्शी प्लेटफ़ॉर्म के माध्यम से जोड़ता है, जहाँ रोज़मर्रा की शहर की समस्याओं की रिपोर्ट और समाधान किया जा सकता है।",

        see_something:
            "कुछ खराब दिखाई दिया?",

        cta_description:
            "इसे नज़रअंदाज़ न करें। इसकी रिपोर्ट करें, अपने समुदाय का समर्थन प्राप्त करें और समस्या को हल कराने में मदद करें।",

        footer_tagline:
            "मिलकर बेहतर शहर बनाएं।"
    }

};



/* =====================================================
   APPLY LANGUAGE
===================================================== */

function applyLanguage(language) {

    const selectedLanguage =
        translations[language]
            ? language
            : "en";


    const elements =
        document.querySelectorAll("[data-i18n]");


    elements.forEach(function(element) {

        const key =
            element.getAttribute("data-i18n");


        if (
            translations[selectedLanguage] &&
            translations[selectedLanguage][key]
        ) {

            element.textContent =
                translations[selectedLanguage][key];

        }

    });


    /* Update language button */

    const languageButton =
        document.getElementById("current-language");


    if (languageButton) {

        languageButton.textContent =
            selectedLanguage === "hi"
                ? "HI"
                : "EN";

    }


    /* Update HTML language */

    document.documentElement.lang =
        selectedLanguage;


    /* Save language */

    localStorage.setItem(
        "fixmycity_language",
        selectedLanguage
    );

}



/* =====================================================
   SET LANGUAGE
===================================================== */

function setLanguage(language) {

    applyLanguage(language);

    closeLanguageMenu();

}



/* =====================================================
   LANGUAGE MENU
===================================================== */

function toggleLanguageMenu() {

    const menu =
        document.getElementById("language-menu");


    if (!menu) {
        return;
    }


    menu.classList.toggle("show");

}



function closeLanguageMenu() {

    const menu =
        document.getElementById("language-menu");


    if (!menu) {
        return;
    }


    menu.classList.remove("show");

}



/* =====================================================
   CLOSE MENU WHEN CLICKING OUTSIDE
===================================================== */

document.addEventListener(
    "click",
    function(event) {

        const selector =
            document.querySelector(
                ".language-selector"
            );


        if (
            selector &&
            !selector.contains(event.target)
        ) {

            closeLanguageMenu();

        }

    }
);



/* =====================================================
   LOAD SAVED LANGUAGE
===================================================== */

document.addEventListener(
    "DOMContentLoaded",
    function() {

        const savedLanguage =
            localStorage.getItem(
                "fixmycity_language"
            ) || "en";


        applyLanguage(savedLanguage);

    }
);