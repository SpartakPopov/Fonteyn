  function startEdit(username) {
            const row = document.getElementById(`row-${username}`);
            row.querySelectorAll(".display").forEach(el => el.style.display = "none");
            row.querySelectorAll(".edit-input").forEach(el => el.style.display = "inline-block");
            row.querySelector(`#save-btn-${username}`).style.display = "inline-block";
            row.querySelector(`#cancel-btn-${username}`).style.display = "inline-block";
            row.querySelector(".edit-btn").style.display = "none";
        }

        function cancelEdit(username) {
            const row = document.getElementById(`row-${username}`);
            row.querySelectorAll(".display").forEach(el => el.style.display = "inline-block");
            row.querySelectorAll(".edit-input").forEach(el => el.style.display = "none");
            row.querySelector(`#save-btn-${username}`).style.display = "none";
            row.querySelector(`#cancel-btn-${username}`).style.display = "none";
            row.querySelector(".edit-btn").style.display = "inline-block";
        }

        async function saveEdit(username) {
            const names = document.getElementById(`input-names-${username}`).value;
            const email = document.getElementById(`input-email-${username}`).value;
            const position = document.getElementById(`input-position-${username}`).value;

            try {
                const response = await fetch(`/edit_employee/${username}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ names, email, position })
                });
                if (response.ok) {
                    document.getElementById(`names-${username}`).textContent = names;
                    document.getElementById(`email-${username}`).textContent = email;
                    document.getElementById(`position-${username}`).textContent = position;
                    cancelEdit(username);
                } else {
                    const error = await response.json();
                    alert(`Failed to save changes: ${error.detail || "Unknown error"}`);
                }
            } catch (err) {
                alert(`Failed to save changes: ${err.message}`);
            }
        }

        async function deleteEmployee(username) {
            if (!confirm(`Are you sure you want to delete employee: ${username}?`)) {
                return;
            }

            try {
                const response = await fetch(`/delete_employee/${username}`, {
                    method: "DELETE"
                });
                if (response.ok) {
                    const row = document.getElementById(`row-${username}`);
                    if (row) row.remove();
                } else {
                    const error = await response.json();
                    alert(`Failed to delete employee: ${error.detail || "Unknown error"}`);
                }
            } catch (err) {
                alert(`Failed to delete employee: ${err.message}`);
            }
        }

        async function approveUser(username) {
            try {
                const response = await fetch(`/approve_user/${username}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });
                const data = await response.json();
                if (data.status === "success") {
                    alert(data.message);
                    const row = document.getElementById(`pending-row-${username}`);
                    if (row) row.remove();
                } else {
                    alert(`Error: ${data.detail}`);
                }
            } catch (err) {
                alert(`Failed to approve user: ${err.message}`);
            }
        }

        async function rejectUser(username) {
            try {
                const response = await fetch(`/reject_user/${username}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });
                const data = await response.json();
                if (data.status === "success") {
                    alert(data.message);
                    const row = document.getElementById(`pending-row-${username}`);
                    if (row) row.remove();
                } else {
                    alert(`Error: ${data.detail}`);
                }
            } catch (err) {
                alert(`Failed to reject user: ${err.message}`);
            }
        }

        document.addEventListener("DOMContentLoaded", () => {
            document.querySelectorAll("tr[data-username]").forEach(row => {
                const username = row.dataset.username;
                row.querySelector(".edit-btn")?.addEventListener("click", () => startEdit(username));
                row.querySelector(".save-btn")?.addEventListener("click", () => saveEdit(username));
                row.querySelector(".cancel-btn")?.addEventListener("click", () => cancelEdit(username));
                row.querySelector(".delete-btn")?.addEventListener("click", () => deleteEmployee(username));
                row.querySelector(".approve-btn")?.addEventListener("click", () => approveUser(username));
                row.querySelector(".reject-btn")?.addEventListener("click", () => rejectUser(username));
            });
        });