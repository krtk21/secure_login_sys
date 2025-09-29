document.getElementById("registrationForm").addEventListener("submit", function (e) {
  const password = document.getElementById("password").value;
  const passwordHelp = document.getElementById("passwordHelp");

  const isValid = /^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?])[A-Za-z\d!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]{8,}$/.test(password);

  if (!isValid) {
    e.preventDefault();
    passwordHelp.style.color = "red";
    alert("Password must be at least 8 characters long, contain 1 uppercase letter, 1 number, and 1 special symbol.");
  } else {
    passwordHelp.style.color = "green";
  }
});
