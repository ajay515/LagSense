const API = "https://lagsense-api.onrender.com";

async function register() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const msg = document.getElementById("message");

  msg.innerText = "";

  if (!email || !password) {
    msg.innerText = "Email and password are required";
    return;
  }

  try {
    const res = await fetch(`${API}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (data.success) {
      // ✅ success → redirect, no message
      window.location.href = "login.html";
    } else {
      // ❌ failure → show backend message
      msg.innerText = data.message || "Registration failed";
    }
  } catch (err) {
    msg.innerText = "Registration error: " + err.message;
    console.error("Register error:", err);
  }
}

async function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const msg = document.getElementById("message");

  msg.innerText = "";

  if (!email || !password) {
    msg.innerText = "Email and password are required";
    return;
  }

  try {
    const res = await fetch(`${API}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    const data = await res.json();

    if (data.success) {
      // ✅ success → store user and redirect
      localStorage.setItem("user_id", data.user_id);
      localStorage.setItem("user_email", email);
      window.location.href = "dashboard.html";
    } else {
      // ❌ failure → show backend message
      msg.innerText = data.message || "Login failed";
    }
  } catch (err) {
    msg.innerText = "Login error: " + err.message;
    console.error("Login error:", err);
  }
}