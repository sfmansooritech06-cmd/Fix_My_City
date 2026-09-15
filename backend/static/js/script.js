// ===============================
// CITIZEN REGISTRATION
// ===============================

const registerForm = document.querySelector(".login-form");

if (registerForm && window.location.pathname.includes("register.html")) {

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

                // Go to login page
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