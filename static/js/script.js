// Campus Linker JavaScript Functions

// Show/Hide Registration Form
function showRegister() {
  document.querySelector(".auth-card:first-child").style.display = "none"
  document.getElementById("register-form").style.display = "block"
}

function showLogin() {
  document.querySelector(".auth-card:first-child").style.display = "block"
  document.getElementById("register-form").style.display = "none"
}

// Form Validation
function validateForm(formId) {
  const form = document.getElementById(formId)
  const inputs = form.querySelectorAll("input[required]")
  let isValid = true

  inputs.forEach((input) => {
    if (!input.value.trim()) {
      input.style.borderColor = "#dc3545"
      isValid = false
    } else {
      input.style.borderColor = "#28a745"
    }
  })

  return isValid
}

// Auto-hide alerts after 5 seconds
document.addEventListener("DOMContentLoaded", () => {
  const alerts = document.querySelectorAll(".alert")
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.opacity = "0"
      setTimeout(() => {
        alert.remove()
      }, 300)
    }, 5000)
  })
})

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault()
    const target = document.querySelector(this.getAttribute("href"))
    if (target) {
      target.scrollIntoView({
        behavior: "smooth",
        block: "start",
      })
    }
  })
})

// Loading animation for forms
function showLoading(button) {
  const originalText = button.textContent
  button.textContent = "Loading..."
  button.disabled = true

  setTimeout(() => {
    button.textContent = originalText
    button.disabled = false
  }, 2000)
}

// Add loading animation to all form submissions
document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", (e) => {
    const submitButton = form.querySelector('button[type="submit"]')
    if (submitButton) {
      showLoading(submitButton)
    }
  })
})
