export function makePasswordToggle() {
    const togglePassword = document.querySelector("#togglePassword");
    if (togglePassword !== null) {
        const password = document.querySelector("#id_password");
        togglePassword.addEventListener("click", function () {
            // toggle the type attribute
            password.setAttribute("type", password.getAttribute("type") === "password" ? "text" : "password");
            // toggle the icon
            this.classList.toggle("fa-eye");
            this.classList.toggle("fa-eye-slash");
        });
    }
}