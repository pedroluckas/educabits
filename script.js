document.getElementById("loginForm").addEventListener("submit", function (e) {
  const email = document.getElementById("email").value;
  const senha = document.getElementById("senha").value;

  if (email.trim() === "" || senha.trim() === "") {
    e.preventDefault();
    alert("Por favor, preencha todos os campos.");
  }
});
