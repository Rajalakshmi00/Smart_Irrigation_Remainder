document.getElementById('login-form').addEventListener('submit', async (event) => {
    event.preventDefault(); // Prevent the default form submission

    const phoneNumber = document.getElementById('phone_number').value;

    try {
        const response = await fetch('http://127.0.0.1:5000/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ phone_number: phoneNumber })
        });

        const data = await response.json();
        const messageDiv = document.getElementById('message');
        
        // Display the message from the server
        messageDiv.textContent = data.message;

        // If login is successful, show a success message and then redirect
        if (data.success) {
            messageDiv.textContent = "Login successful! Redirecting to home page...";
            messageDiv.style.color = "green"; // Change the text color to green for success indication

            // Delay redirection to home page by 2 seconds to allow user to see the message
            setTimeout(() => {
                window.location.href = 'home.html'; // Ensure this path is correct
            }, 2000); // 2 second delay
        }

    } catch (error) {
        console.error('Error:', error);
        document.getElementById('message').textContent = 'An error occurred. Please try again.';
        messageDiv.style.color = "red"; // Set color to red for errors
    }
});
