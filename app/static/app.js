// Simple frontend: talks to the FastAPI backend using fetch().

const $ = (id) => document.getElementById(id);
let students = [];   // all students loaded from the server

// ---------- small helpers ----------
function esc(text) {                       // makes text safe to show in HTML
  const d = document.createElement("div");
  d.textContent = text ?? "";
  return d.innerHTML;
}

function formatDate(iso) {
  if (!iso) return "-";
  return new Date(iso + "T00:00:00").toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function toast(message, isError = false) {
  const t = $("toast");
  t.textContent = message;
  t.className = "show" + (isError ? " error" : "");
  setTimeout(() => (t.className = ""), 3000);
}

// Turn server errors into a friendly sentence
function errorMessage(data) {
  if (Array.isArray(data.detail)) {
    return data.detail.map((e) => {
      const field = e.loc[e.loc.length - 1];
      const msg = e.msg.replace("Value error, ", "");
      return field === "body" ? msg : `${field}: ${msg}`;
    }).join(". ");
  }
  return data.detail || "Something went wrong";
}

async function request(url, options = {}) {
  const res = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(errorMessage(data));
  return data;
}

// ---------- page switching ----------
function showPage(name) {
  document.querySelectorAll(".page").forEach((p) => p.classList.toggle("hidden", p.id !== "page-" + name));
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.toggle("active", b.dataset.page === name));
}
document.querySelectorAll(".nav-btn").forEach((b) => b.addEventListener("click", () => showPage(b.dataset.page)));

// ---------- load data ----------
async function loadStudents() {
  students = await request("/students?limit=500");
  renderDashboard();
  fillCourseFilter();
  renderTable();
}

// ---------- dashboard ----------
function initials(name) {
  return name.split(" ").filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
}

function renderDashboard() {
  const perCourse = {};
  students.forEach((s) => {
    const c = s.course || "No course";
    perCourse[c] = (perCourse[c] || 0) + 1;
  });
  const year = String(new Date().getFullYear());
  const cards = [
    ["Total students", students.length],
    ["Courses", Object.keys(perCourse).filter((c) => c !== "No course").length],
    ["Enrolled this year", students.filter((s) => (s.enrollment_date || "").startsWith(year)).length],
    ["Have email", students.filter((s) => s.email).length],
  ];
  $("stats").innerHTML = cards.map(([label, num]) =>
    `<div class="card"><div class="num">${num}</div><div class="label">${label}</div></div>`).join("");

  const max = Math.max(1, ...Object.values(perCourse));
  $("courseBars").innerHTML = Object.entries(perCourse).map(([course, n]) =>
    `<div class="bar-row">
       <div class="bar-top"><span>${esc(course)}</span><b>${n}</b></div>
       <div class="bar"><span style="width:${(n / max) * 100}%"></span></div>
     </div>`).join("") || `<p class="muted">No data yet.</p>`;

  const recent = [...students].sort((a, b) => b.id - a.id).slice(0, 5);
  $("recentList").innerHTML = recent.map((s) =>
    `<li><div class="avatar">${esc(initials(s.name))}</div>
       <div><div>${esc(s.name)}</div><div class="muted small">${esc(s.course || "No course")}</div></div></li>`
  ).join("") || `<p class="muted">No students yet. Click "Add Student".</p>`;
}

// ---------- students table ----------
function fillCourseFilter() {
  const courses = [...new Set(students.map((s) => s.course).filter(Boolean))].sort();
  const selected = $("courseFilter").value;
  $("courseFilter").innerHTML = `<option value="">All courses</option>` +
    courses.map((c) => `<option ${c === selected ? "selected" : ""}>${esc(c)}</option>`).join("");
  $("courseList").innerHTML = courses.map((c) => `<option value="${esc(c)}">`).join("");
}

function renderTable() {
  const q = $("search").value.trim().toLowerCase();
  const course = $("courseFilter").value;
  const rows = students.filter((s) =>
    (!q || s.name.toLowerCase().includes(q) || (s.email || "").toLowerCase().includes(q)) &&
    (!course || s.course === course));

  $("studentsBody").innerHTML = rows.map((s) =>
    `<tr>
       <td><div class="name-cell"><div class="avatar">${esc(initials(s.name))}</div><b>${esc(s.name)}</b></div></td>
       <td>${s.course ? `<span class="tag">${esc(s.course)}</span>` : "-"}</td>
       <td>${formatDate(s.date_of_birth)}</td>
       <td>${esc(s.email || "")}${s.email && s.phone ? "<br>" : ""}<span class="muted">${esc(s.phone || "")}</span></td>
       <td class="actions">
         <button class="btn small-btn" data-edit="${s.id}">Edit</button>
         <button class="btn small-btn danger" data-delete="${s.id}">Delete</button>
       </td>
     </tr>`).join("");

  $("emptyState").classList.toggle("hidden", rows.length > 0);
  $("count").textContent = `(${rows.length})`;
}

$("search").addEventListener("input", renderTable);
$("courseFilter").addEventListener("change", renderTable);

// Edit / Delete buttons (one listener for the whole table)
$("studentsBody").addEventListener("click", async (e) => {
  const editId = e.target.dataset.edit;
  const deleteId = e.target.dataset.delete;
  if (editId) openForm(students.find((s) => s.id == editId));
  if (deleteId) {
    const s = students.find((x) => x.id == deleteId);
    if (!confirm(`Delete ${s.name}? This cannot be undone.`)) return;
    try {
      await request(`/students/${deleteId}`, { method: "DELETE" });
      toast("Student deleted");
      loadStudents();
    } catch (err) { toast(err.message, true); }
  }
});

// ---------- add / edit form ----------
function openForm(student = null) {
  $("studentForm").reset();
  $("formError").classList.add("hidden");
  $("dialogTitle").textContent = student ? "Edit Student" : "Add Student";
  $("studentId").value = student ? student.id : "";
  if (student) {
    $("name").value = student.name;
    $("dob").value = student.date_of_birth;
    $("email").value = student.email || "";
    $("phone").value = student.phone || "";
    $("course").value = student.course || "";
    $("enrolled").value = student.enrollment_date || "";
    $("address").value = student.address || "";
  }
  $("studentDialog").showModal();
}

$("addBtn").addEventListener("click", () => openForm());
$("quickAdd").addEventListener("click", () => openForm());
$("cancelBtn").addEventListener("click", () => $("studentDialog").close());

$("studentForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const id = $("studentId").value;
  const data = {
    name: $("name").value,
    date_of_birth: $("dob").value,
    email: $("email").value.trim() || null,
    phone: $("phone").value.trim() || null,
    course: $("course").value.trim() || null,
    enrollment_date: $("enrolled").value || null,
    address: $("address").value.trim() || null,
  };
  try {
    await request(id ? `/students/${id}` : "/students", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(data),
    });
    $("studentDialog").close();
    toast(id ? "Student updated" : "Student added");
    loadStudents();
  } catch (err) {
    $("formError").textContent = err.message;
    $("formError").classList.remove("hidden");
  }
});

// ---------- Ask AI ----------
async function askAI() {
  const question = $("question").value.trim();
  if (question.length < 3) return;
  const box = $("answer");
  box.className = "answer";
  box.textContent = "Thinking...";
  try {
    const data = await request("/ai/ask", { method: "POST", body: JSON.stringify({ question }) });
    box.textContent = data.answer;
  } catch (err) {
    box.className = "answer error";
    box.textContent = err.message;
  }
}
$("askBtn").addEventListener("click", askAI);
$("question").addEventListener("keydown", (e) => { if (e.key === "Enter") askAI(); });
document.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => {
  $("question").value = c.textContent;
  askAI();
}));

// ---------- start ----------
loadStudents().catch((err) => toast(err.message, true));
