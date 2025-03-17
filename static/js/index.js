const wrapper = document.querySelector('.wrapper');
const registerLink = document.querySelector('.register-link');
const loginLink = document.querySelector('.login-link');

// Get the correct hidden input for each form
const loginActionInput = document.querySelector('.login input[name="action"]');
const signupActionInput = document.querySelector('.register input[name="action"]');

// Select submit buttons inside the respective forms
const loginButton = document.querySelector('.login button[type="submit"]');
const signupButton = document.querySelector('.register button[type="submit"]');

// Get confirm password field inside signup form only
const confirmPasswordBox = document.querySelector('.register #confirm-password');

registerLink.onclick = () => {
    wrapper.classList.add('active');
    
    // Set correct action for signup form
    signupActionInput.value = 'signup';

    // Show confirm password field
    if (confirmPasswordBox) {
        confirmPasswordBox.style.display = 'block';
    }

    // Update button text
    signupButton.textContent = 'Sign Up';
};

loginLink.onclick = () => {
    wrapper.classList.remove('active');

    // Set correct action for login form
    loginActionInput.value = 'login';

    // Hide confirm password field
    if (confirmPasswordBox) {
        confirmPasswordBox.style.display = 'none';
    }

    // Update button text
    loginButton.textContent = 'Login';
};


document.addEventListener("DOMContentLoaded", () => {
    const loginButton = document.querySelector('.login .btn');
    const signupButton = document.querySelector('.register .btn');

    // Debug login button click
    loginButton.addEventListener("click", (event) => {
        event.preventDefault(); // Prevent form submission temporarily
        document.querySelector('.login form').submit();  // Submit the login form explicitly
        console.log("Login button clicked.");
    });

    // Debug signup button click
    signupButton.addEventListener("click", (event) => {
        event.preventDefault(); // Prevent form submission temporarily
        document.querySelector('.register form').submit();  // Submit the signup form explicitly
        console.log("Sign Up button clicked.");
    });
});

