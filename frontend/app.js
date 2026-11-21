"use strict";

const API_URL = "http://127.0.0.1:5000/api/tasks";
const STATUS_LABELS = {
  todo: "To do",
  in_progress: "In progress",
  done "Completed",
};

const taskList = document.querySelector("#task-list");
const taskForm = document.querySelector("#task-form");
const notice = document.querySelector("#notice");
const refreshButton = document.querySelector("#refresh-button");
const submitButton = document.querySelector("#submit-button");
let noticeTimeout;

function showNotice(message, type) {
  window.clearTimeout(noticeTimeout);
  notice.textContent = message;
  notice.className = `notice notice-${type}`;
  notice.hidden = false;
  noticeTimeout = window.setTimeout(() => {
    notice.hidden = true;
  }, 5000);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new Error("The server returned an unreadable response.");
  }

  if (!response.ok) {
    throw new Error(payload.error || `Request failed (${response.status}).`);
  }
  return payload;
}

function updateSummary(tasks) {
  document.querySelector("#total-count").textContent = String(tasks.length);
  document.querySelector("#progress-count").textContent = String(
    tasks.filter((task) => task.status === "in_progress").length,
  );
  document.querySelector("#completed-count").textContent = String(
    tasks.filter((task) => task.status === "done").length,
  );
}

function makeStateMessage(title, detail) {
  const state = document.createElement("div");
  state.className = "state-message";
  const heading = document.createElement("strong");
  heading.textContent = title;
  const description = document.createElement("p");
  description.textContent = detail;
  state.append(heading, description);
  return state;
}

function makeTaskCard(task) {
  const card = document.createElement("article");
  card.className = "task-card";

  const content = document.createElement("div");
  content.className = "task-card-content";
  const title = document.createElement("h3");
  title.className = "task-title";
  title.textContent = task.title;
  content.append(title);

  if (task.description) {
    const description = document.createElement("p");
    description.className = "task-description";
    description.textContent = task.description;
    content.append(description);
  }

  const meta = document.createElement("div");
  meta.className = "task-meta";
  const created = new Date(task.created_at);
  const date = document.createElement("span");
  date.textContent = Number.isNaN(created.getTime())
    ? "Created recently"
    : `Created ${created.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: "numeric",
      })}`;
  const statusText = document.createElement("span");
  statusText.textContent = STATUS_LABELS[task.status] || "Unknown status";
  meta.append(date, statusText);
  content.append(meta);

  const controls = document.createElement("div");
  controls.className = "task-controls";

  const status = document.createElement("select");
  status.className = "status-select";
  status.setAttribute("aria-label", `Update status for ${task.title}`);
  Object.entries(STATUS_LABELS).forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;
    status.append(option);
  });
  status.value = task.status;
  status.addEventListener("change", () => updateTaskStatus(task, status));

  const remove = document.createElement("button");
  remove.className = "delete-button";
  remove.type = "button";
  remove.textContent = "×";
  remove.setAttribute("aria-label", `Delete ${task.title}`);
  remove.addEventListener("click", () => deleteTask(task, remove));
  controls.append(status, remove);

  card.append(content, controls);
  return card;
}

function renderTasks(tasks) {
  updateSummary(tasks);
  taskList.replaceChildren();

  if (tasks.length === 0) {
    taskList.append(
      makeStateMessage("Nothing on your list yet", "Create a task to get your day started."),
    );
    return;
  }

  tasks.forEach((task) => taskList.append(makeTaskCard(task)));
}

async function loadTasks(showLoading = true) {
  refreshButton.disabled = true;
  if (showLoading) {
    taskList.replaceChildren();
    const state = document.createElement("div");
    state.className = "state-message";
    const spinner = document.createElement("span");
    spinner.className = "spinner";
    spinner.setAttribute("aria-hidden", "true");
    const message = document.createElement("p");
    message.textContent = "Loading your tasks…";
    state.append(spinner, message);
    taskList.append(state);
  }

  try {
    const tasks = await requestJson(API_URL);
    renderTasks(tasks);
  } catch (error) {
    updateSummary([]);
    taskList.replaceChildren(
      makeStateMessage("Couldn’t load your tasks", error.message),
    );
    showNotice(error.message, "error");
  } finally {
    refreshButton.disabled = false;
  }
}

async function updateTaskStatus(task, select) {
  const previousStatus = task.status;
  select.disabled = true;
  try {
    await requestJson(`${API_URL}/${task.id}`, {
      method: "PUT",
      body: JSON.stringify({ status: select.value }),
    });
    showNotice("Task status updated.", "success");
    await loadTasks(false);
  } catch (error) {
    select.value = previousStatus;
    showNotice(error.message, "error");
  } finally {
    select.disabled = false;
  }
}

async function deleteTask(task, button) {
  button.disabled = true;
  try {
    await requestJson(`${API_URL}/${task.id}`, { method: "PATCH" });
    showNotice("Task deleted.", "success");
    await loadTasks(false);
  } catch (error) {
    button.disabled = false;
    showNotice(error.message, "error");
  }
}

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!taskForm.reportValidity()) {
    return;
  }

  const formData = new FormData(taskForm);
  const payload = {
    title: formData.get("title").trim(),
    description: formData.get("description").trim(),
    status: formData.get("status"),
  };
  submitButton.disabled = true;

  try {
    await requestJson(API_URL, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    taskForm.reset();
    showNotice("Task created successfully.", "success");
    await loadTasks(false);
  } catch (error) {
    showNotice(error.message, "error");
  } finally {
    submitButton.disabled = false;
  }
});

refreshButton.addEventListener("click", () => loadTasks());
document.querySelector("#today-date").textContent = new Date().toLocaleDateString(
  undefined,
  { weekday: "short", month: "short", day: "numeric" },
);
loadTasks();
